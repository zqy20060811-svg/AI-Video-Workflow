<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>项目列表</span>
        <el-button type="primary" @click="router.push('/projects/new')">新建项目</el-button>
        <el-button @click="router.push('/settings')">模型设置</el-button>
      </div>
    </template>
    <el-table :data="projects" v-loading="loading" empty-text="暂无项目，点击右上角新建">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="aspect_ratio" label="画幅" width="100" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button text type="primary" @click="router.push(`/projects/${row.id}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, type Project } from '../api/projects'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await listProjects()
    projects.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
