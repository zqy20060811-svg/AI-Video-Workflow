<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="brand" @click="router.push('/')">AI 视频生产工作流</div>
      <el-button type="primary" text @click="router.push('/projects/new')">新建项目</el-button>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style>
body {
  margin: 0;
  background: #f5f7fa;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}
.layout {
  min-height: 100vh;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
}
.brand {
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
}
</style>
