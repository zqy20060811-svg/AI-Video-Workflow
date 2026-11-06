<template>
  <el-card style="max-width: 640px">
    <template #header>新建项目</template>
    <el-form :model="form" label-width="90px">
      <el-form-item label="项目名称" required>
        <el-input v-model="form.name" placeholder="例如：最后的列车" />
      </el-form-item>
      <el-form-item label="剧情概要">
        <el-input v-model="form.story" type="textarea" :rows="6" placeholder="一句话或一段话描述你的故事" />
      </el-form-item>
      <el-form-item label="画幅比例">
        <el-radio-group v-model="form.aspect_ratio">
          <el-radio-button value="9:16">9:16 竖屏</el-radio-button>
          <el-radio-button value="16:9">16:9 横屏</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">创建</el-button>
        <el-button @click="router.push('/')">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createProject } from '../api/projects'

const router = useRouter()
const submitting = ref(false)
const form = reactive({ name: '', story: '', aspect_ratio: '9:16' })

async function onSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写项目名称')
    return
  }
  submitting.value = true
  try {
    const res = await createProject({ name: form.name.trim(), story: form.story, aspect_ratio: form.aspect_ratio })
    ElMessage.success('创建成功')
    router.push(`/projects/${res.data.id}`)
  } finally {
    submitting.value = false
  }
}
</script>
