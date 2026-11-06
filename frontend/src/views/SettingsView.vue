<template>
  <div>
    <el-card>
      <template #header>
        <div class="row">
          <span>模型设置</span>
          <div class="spacer" />
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="模型全部通过 backend/.env 配置，修改后重启后端生效；业务代码不耦合任何具体模型。"
      />
    </el-card>

    <div v-loading="loading" class="cards">
      <el-card class="config-card">
        <template #header>LLM（故事分析 / 分镜生成）</template>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="Provider">OpenAI 兼容 API</el-descriptions-item>
          <el-descriptions-item label="地址">{{ config?.llm.base_url }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ config?.llm.model }}</el-descriptions-item>
        </el-descriptions>
        <p class="hint">配置项：LLM_BASE_URL / LLM_MODEL / LLM_API_KEY</p>
      </el-card>

      <el-card class="config-card">
        <template #header>
          <div class="row">
            图片生成
            <el-tag size="small" :type="config?.image.configured ? 'success' : 'warning'">
              {{ config?.image.configured ? '已配置' : '未配置' }}
            </el-tag>
          </div>
        </template>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="Provider">{{ config?.image.provider }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ config?.image.model || '（模板默认）' }}</el-descriptions-item>
          <el-descriptions-item label="ComfyUI">{{ config?.comfyui_url }}</el-descriptions-item>
        </el-descriptions>
        <el-alert
          v-if="config && !config.image.configured"
          type="warning"
          :closable="false"
          show-icon
          class="hint"
          title="当前未配置图片生成模型。你可以：1. 在 .env 设置 IMAGE_PROVIDER=pollinations（免费、无需 Key，推荐）；2. 本地安装 ComfyUI 并设置 IMAGE_PROVIDER=comfyui；3. 使用外部工具生成后手动上传。"
        />
        <p class="hint">配置项：IMAGE_PROVIDER / IMAGE_MODEL / COMFYUI_URL</p>
      </el-card>

      <el-card class="config-card">
        <template #header>
          <div class="row">
            视频生成（Image-to-Video）
            <el-tag size="small" :type="config?.video.configured ? 'success' : 'warning'">
              {{ config?.video.configured ? '已配置' : '未配置' }}
            </el-tag>
          </div>
        </template>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="Provider">{{ config?.video.provider }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ config?.video.model || '（模板默认）' }}</el-descriptions-item>
          <el-descriptions-item label="CLIP / VAE">
            {{ config?.video.clip_model || '（模板默认）' }} / {{ config?.video.vae_model || '（模板默认）' }}
          </el-descriptions-item>
          <el-descriptions-item label="帧率">{{ config?.video.fps }} fps</el-descriptions-item>
        </el-descriptions>
        <el-alert
          v-if="config && !config.video.configured"
          type="warning"
          :closable="false"
          show-icon
          class="hint"
          title="当前未配置视频生成模型。你可以：1. 本地安装 ComfyUI + LTX-Video 等开源 I2V 模型，并在 .env 设置 VIDEO_PROVIDER=comfyui；2. 配置其他视频模型 API。"
        />
        <p class="hint">配置项：VIDEO_PROVIDER / VIDEO_MODEL / VIDEO_CLIP_MODEL / VIDEO_VAE_MODEL / COMFYUI_URL</p>
      </el-card>
    </div>

    <el-card>
      <template #header>
        <div class="row">
          <span>本地生成环境</span>
          <div class="spacer" />
          <el-button type="primary" size="small" :loading="checking" @click="onCheckEnv">
            检查本地生成环境
          </el-button>
        </div>
      </template>
      <el-descriptions v-if="env" :column="1" border size="small">
        <el-descriptions-item label="GPU">
          <template v-if="env.gpu.available">
            {{ env.gpu.name }}（显存 {{ env.gpu.vram }}，驱动 {{ env.gpu.driver }}）
          </template>
          <template v-else>未检测到 NVIDIA GPU：{{ env.gpu.detail }}</template>
        </el-descriptions-item>
        <el-descriptions-item label="PyTorch">
          <template v-if="env.pytorch.installed">
            {{ env.pytorch.version }}，CUDA {{ env.pytorch.cuda_available ? '可用' : '不可用' }}
          </template>
          <template v-else>未安装（通过 ComfyUI 生成不受影响）</template>
        </el-descriptions-item>
        <el-descriptions-item label="ComfyUI">
          <template v-if="env.comfyui.reachable">
            已连接（{{ env.comfyui.url }}）
            <el-tag v-if="env.comfyui.image_model_ready === true" type="success" size="small">图片模型就绪</el-tag>
            <el-tag v-else-if="env.comfyui.image_model_ready === false" type="danger" size="small">
              IMAGE_MODEL 不在已装模型列表
            </el-tag>
            <el-tag v-if="env.comfyui.video_model_ready === true" type="success" size="small">视频模型就绪</el-tag>
            <el-tag v-else-if="env.comfyui.video_model_ready === false" type="danger" size="small">
              VIDEO_MODEL 不在已装模型列表
            </el-tag>
          </template>
          <template v-else>未连接：{{ env.comfyui.detail }}</template>
        </el-descriptions-item>
      </el-descriptions>
      <p v-else class="hint">点击「检查本地生成环境」查看 GPU / 显存 / ComfyUI 连接状态与模型就绪情况。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { checkEnv, getModelConfig, type EnvCheck, type ModelConfig } from '../api/system'

const router = useRouter()
const config = ref<ModelConfig | null>(null)
const env = ref<EnvCheck | null>(null)
const loading = ref(false)
const checking = ref(false)

async function load() {
  loading.value = true
  try {
    config.value = (await getModelConfig()).data
  } finally {
    loading.value = false
  }
}

async function onCheckEnv() {
  checking.value = true
  try {
    env.value = (await checkEnv()).data
  } catch {
    env.value = null
  } finally {
    checking.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.spacer {
  flex: 1;
}
.cards {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.hint {
  margin-top: 12px;
  color: #909399;
  font-size: 12px;
  white-space: pre-wrap;
}
</style>
