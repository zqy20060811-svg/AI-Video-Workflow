<template>
  <div v-if="project">
    <el-card>
      <template #header>
        <div class="row">
          <span>{{ project.name }}</span>
          <el-tag>{{ project.status }}</el-tag>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="画幅">{{ project.aspect_ratio }}</el-descriptions-item>
        <el-descriptions-item label="镜头数量">{{ project.shot_count }}</el-descriptions-item>
        <el-descriptions-item label="角色数量">{{ project.characters.length }}</el-descriptions-item>
      </el-descriptions>
      <h4>剧情概要</h4>
      <p>{{ project.story || '（未填写）' }}</p>
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
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createCharacter, getProject, type ProjectDetail } from '../api/projects'

const route = useRoute()
const project = ref<ProjectDetail | null>(null)
const uploading = ref(false)
const charForm = reactive({
  name: '',
  description: '',
  front_image: null as File | null,
  side_image: null as File | null,
  back_image: null as File | null
})

function onPick(field: 'front_image' | 'side_image' | 'back_image', e: Event) {
  const files = (e.target as HTMLInputElement).files
  charForm[field] = files && files.length ? files[0] : null
}

async function load() {
  const res = await getProject(route.params.id as string)
  project.value = res.data
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
</style>
