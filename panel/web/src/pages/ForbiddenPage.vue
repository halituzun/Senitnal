<template>
  <div class="forbidden-wrap">
    <div class="code">403</div>
    <div class="msg">Access Forbidden</div>
    <div class="sub">Cloudflare Access authentication required.</div>
    <router-link to="/login">Back to login</router-link>
  </div>
</template>

<style scoped>
.forbidden-wrap { min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; }
.code { font-size:72px; font-weight:800; color:var(--error); }
.msg { font-size:20px; font-weight:600; }
.sub { color:var(--text-muted); }
</style>
