<template>
  <div class="app-shell">
    <router-view />
  </div>
</template>

<style>
.app-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 0% 0%, rgba(255, 183, 120, 0.28), transparent 32%),
    radial-gradient(circle at 100% 100%, rgba(224, 122, 63, 0.18), transparent 28%),
    linear-gradient(180deg, #f8ede3 0%, #f3e3d3 45%, #edd9c8 100%);
  color: #3d2c21;
}
</style>
