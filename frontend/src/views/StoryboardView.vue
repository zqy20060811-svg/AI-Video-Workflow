<template>
  <div v-if="project">
    <el-card>
      <template #header>
        <div class="row">
          <span>分镜管理 - {{ project.name }}</span>
          <el-tag :type="statusTagType(project.status)">{{ statusLabel(project.status) }}</el-tag>
          <div class="spacer" />
          <el-button @click="router.push(`/projects/${project.id}`)">返回项目</el-button>
        </div>
      </template>
      <p class="story">{{ project.story }}</p>
    </el-card>

    <div v-loading="loading" class="shots">
      <el-card v-for="(shot, index) in shots" :key="shot.id" class="shot-card">
        <template #header>
          <div class="row">
            <b>Shot {{ String(shot.shot_no).padStart(2, '0') }}</b>
            <el-tag size="small" :type="shot.status === 'confirmed' ? 'success' : 'info'">
              {{ shot.status === 'confirmed' ? '已确认' : '草稿' }}
            </el-tag>
            <div class="spacer" />
            <el-button text :disabled="index === 0" @click="move(index, -1)">上移</el-button>
            <el-button text :disabled="index === shots.length - 1" @click="move(index, 1)">下移</el-button>
          </div>
        </template>

        <el-form label-width="90px" size="small">
          <div class="grid3">
            <el-form-item label="场景">
              <el-input v-model="shot.scene" />
            </el-form-item>
            <el-form-item label="地点">
              <el-input v-model="shot.location" />
            </el-form-item>
            <el-form-item label="时间">
              <el-input v-model="shot.time" />
            </el-form-item>
            <el-form-item label="人物">
              <el-input v-model="charactersText[index]" placeholder="多个角色用逗号分隔" />
            </el-form-item>
            <el-form-item label="镜头">
              <el-input v-model="shot.camera" />
            </el-form-item>
            <el-form-item label="时长(秒)">
              <el-input-number v-model="shot.duration" :min="1" :max="30" />
            </el-form-item>
          </div>
          <el-form-item label="动作">
            <el-input v-model="shot.action" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="画面描述">
            <el-input v-model="shot.visual_description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="台词">
            <el-input v-model="shot.dialogue" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="Image Prompt">
            <el-input v-model="shot.image_prompt" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="Video Prompt">
            <el-input v-model="shot.video_prompt" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>

        <div class="row">
          <el-button type="primary" size="small" :loading="savingId === shot.id" @click="onSaveShot(shot, index)">
            保存
          </el-button>
          <el-popconfirm title="确定删除该分镜？" @confirm="onDeleteShot(shot)">
            <template #reference>
              <el-button type="danger" size="plain">删除</el-button>
            </template>
          </el-popconfirm>
        </div>
      </el-card>
    </div>

    <div class="bottom-bar">
      <el-button :loading="adding" @click="onAddShot">＋新增分镜</el-button>
      <el-button type="success" :loading="confirming" :disabled="shots.length === 0" @click="onConfirm">
        确认全部分镜
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  confirmStoryboard,
  createShot,
  deleteShot,
  getProject,
  reorderShots,
  updateShot,
  type ProjectDetail,
  type Shot
} from '../api/projects'

const route = useRoute()
const router = useRouter()
const project = ref<ProjectDetail | null>(null)
const shots = ref<Shot[]>([])
const loading = ref(false)
const savingId = ref<number | null>(null)
const adding = ref(false)
const confirming = ref(false)

// characters JSON 数组与逗号分隔文本的双向绑定辅助
const charactersText = ref<string[]>([])

function syncCharactersText() {
  charactersText.value = shots.value.map((s) => (s.characters || []).join('，'))
}

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

const projectId = computed(() => route.params.id as string)

async function load() {
  loading.value = true
  try {
    const res = await getProject(projectId.value)
    project.value = res.data
    shots.value = [...res.data.shots].sort((a, b) => a.shot_no - b.shot_no)
    syncCharactersText()
  } finally {
    loading.value = false
  }
}

function shotPayload(shot: Shot, index: number) {
  return {
    scene: shot.scene,
    location: shot.location,
    time: shot.time,
    characters: charactersText.value[index]
      ? charactersText.value[index]
          .split(/[，,]/)
          .map((s) => s.trim())
          .filter(Boolean)
      : [],
    action: shot.action,
    camera: shot.camera,
    visual_description: shot.visual_description,
    dialogue: shot.dialogue,
    duration: shot.duration,
    image_prompt: shot.image_prompt,
    video_prompt: shot.video_prompt
  }
}

async function onSaveShot(shot: Shot, index: number) {
  savingId.value = shot.id
  try {
    const res = await updateShot(shot.id, shotPayload(shot, index))
    Object.assign(shot, res.data)
    ElMessage.success(`Shot ${String(shot.shot_no).padStart(2, '0')} 已保存`)
    await load()
  } finally {
    savingId.value = null
  }
}

async function onDeleteShot(shot: Shot) {
  await deleteShot(shot.id)
  ElMessage.success('分镜已删除')
  await load()
}

async function onAddShot() {
  adding.value = true
  try {
    await createShot(projectId.value, { scene: '新场景' })
    ElMessage.success('已新增分镜')
    await load()
  } finally {
    adding.value = false
  }
}

// 上移/下移：本地交换后统一提交 reorder
async function move(index: number, dir: -1 | 1) {
  const target = index + dir
  if (target < 0 || target >= shots.value.length) return
  const arr = [...shots.value]
  ;[arr[index], arr[target]] = [arr[target], arr[index]]
  await reorderShots(
    projectId.value,
    arr.map((s, i) => ({ id: s.id, shot_no: i + 1 }))
  )
  await load()
}

async function onConfirm() {
  confirming.value = true
  try {
    const res = await confirmStoryboard(projectId.value)
    ElMessage.success(`${res.data.message}（共 ${res.data.shot_count} 个镜头）`)
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '确认失败，请重试')
  } finally {
    confirming.value = false
  }
}

watch(projectId, load)
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
.story {
  color: #606266;
  white-space: pre-wrap;
  margin: 0;
}
.shots {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 120px;
}
.grid3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  column-gap: 16px;
}
.bottom-bar {
  margin: 24px 0;
  display: flex;
  gap: 12px;
}
</style>
