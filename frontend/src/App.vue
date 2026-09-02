<template>
  <div class="app-container">
    <NavBar />
    <main class="app-main">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

<script setup>
// 根组件：整体布局（导航栏 + 页面内容 + 页脚）
import Footer from './components/Footer.vue'
import NavBar from './components/NavBar.vue'
</script>
