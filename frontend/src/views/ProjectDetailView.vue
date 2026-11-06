<template>
  <div v-if="project">
    <el-card>
      <template #header>
        <div class="row">
          <span>{{ project.name }}</span>
          <el-tag :type="statusTagType(project.status)">{{ statusLabel(project.status) }}</el-tag>
          <div class="spacer" />
          <el-button
            v-if="project.shot_count > 0"
            @click="router.push(`/projects/${project.id}/storyboard`)"
          >
            查看分镜
          </el-button>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="画幅">{{ project.aspect_ratio }}</el-descriptions-item>
        <el-descriptions-item label="镜头数量">{{ project.shot_count }}</el-descriptions-item>
        <el-descriptions-item label="角色数量">{{ project.characters.length }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <h4>故事梗概</h4>
      <el-input
        v-model="storyDraft"
        type="textarea"
        :rows="6"
        placeholder="写下你的故事梗概，例如：一个女孩深夜来到废弃车站……"
      />
      <div class="row" style="margin-top: 12px">
        <el-button :loading="savingStory" @click="onSaveStory">保存故事</el-button>
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!storyDraft.trim()"
          @click="onGenerate"
        >
          生成分镜
        </el-button>
        <span v-if="generating" class="hint">AI 正在分析故事并生成分镜，请耐心等待（约 1-3 分钟）…</span>
      </div>

      <template v-if="project.story_analysis">
        <el-divider />
        <h4>AI 故事分析</h4>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="标题">{{ analysis.title || '—' }}</el-descriptions-item>
          <el-descriptions-item label="摘要">{{ analysis.summary || '—' }}</el-descriptions-item>
          <el-descriptions-item label="核心冲突">{{ analysis.main_conflict || '—' }}</el-descriptions-item>
          <el-descriptions-item label="关键事件">
            <div v-for="(e, i) in analysis.key_events || []" :key="i">{{ e }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>角色列表</template>
      <el-table :data="project.characters" empty-text="暂无角色">
        <el-table-column prop="name" label="角色名" width="160" />
        <el-table-column prop="description" label="描述" />
      </el-table>

      <el-divider />

      <h4>添加角色（三面图）</h4>
      <el-form :model="charForm" label-width="90px" style="max-width: 560px">
        <el-form-item label="角色名" required>
          <el-input v-model="charForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="charForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="正面图" required>
          <input type="file" accept="image/*" @change="(e) => onPick('front_image', e)" />
        </el-form-item>
        <el-form-item label="侧面图" required>
          <input type="file" accept="image/*" @change="(e) => onPick('side_image', e)" />
        </el-form-item>
        <el-form-item label="背面图" required>
          <input type="file" accept="image/*" @change="(e) => onPick('back_image', e)" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="uploading" @click="onUpload">上传角色</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  createCharacter,
  generateStoryboard,
  getProject,
  updateProject,
  type ProjectDetail
} from '../api/projects'

const route = useRoute()
const router = useRouter()
const project = ref<ProjectDetail | null>(null)
const uploading = ref(false)
const savingStory = ref(false)
const generating = ref(false)
const storyDraft = ref('')

const charForm = reactive({
  name: '',
  description: '',
  front_image: null as File | null,
  side_image: null as File | null,
  back_image: null as File | null
})

// 故事分析结果的便捷访问
const analysis = computed<Record<string, any>>(() => {
  return (project.value?.story_analysis as Record<string, any>) || {}
})

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  story_analyzing: '故事分析中',
  storyboard_generated: '分镜已生成',
  storyboard_reviewing: '分镜审核中',
  storyboard_confirmed: '分镜已确认'
}

const STATUS_TYPES: Record<string, string> = {
  draft: 'info',
  story_analyzing: 'warning',
  storyboard_generated: 'primary',
  storyboard_reviewing: 'warning',
  storyboard_confirmed: 'success'
}

function statusLabel(s: string) {
  return STATUS_LABELS[s] || s
}

function statusTagType(s: string) {
  return (STATUS_TYPES[s] || 'info') as any
}

function onPick(field: 'front_image' | 'side_image' | 'back_image', e: Event) {
  const files = (e.target as HTMLInputElement).files
  charForm[field] = files && files.length ? files[0] : null
}

async function load() {
  const res = await getProject(route.params.id as string)
  project.value = res.data
  storyDraft.value = res.data.story || ''
}

async function onSaveStory() {
  if (!project.value) return
  savingStory.value = true
  try {
    await updateProject(project.value.id, { story: storyDraft.value })
    ElMessage.success('故事已保存')
    await load()
  } finally {
    savingStory.value = false
  }
}

async function onGenerate() {
  if (!project.value) return
  generating.value = true
  try {
    // 生成分镜前自动保存最新故事
    await updateProject(project.value.id, { story: storyDraft.value })
    await generateStoryboard(project.value.id)
    ElMessage.success('分镜生成完成')
    router.push(`/projects/${project.value.id}/storyboard`)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' && detail ? detail : '生成失败，请重试')
  } finally {
    generating.value = false
  }
}

async function onUpload() {
  if (!charForm.name.trim() || !charForm.front_image || !charForm.side_image || !charForm.back_image) {
    ElMessage.warning('请填写角色名并选择三张图片')
    return
  }
  uploading.value = true
  try {
    await createCharacter(route.params.id as string, {
      name: charForm.name.trim(),
      description: charForm.description,
      front_image: charForm.front_image,
      side_image: charForm.side_image,
      back_image: charForm.back_image
    })
    ElMessage.success('角色已添加')
    charForm.name = ''
    charForm.description = ''
    charForm.front_image = charForm.side_image = charForm.back_image = null
    await load()
  } finally {
    uploading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.spacer {
  flex: 1;
}
.hint {
  color: #909399;
  font-size: 13px;
}
</style>
