<template>
  <div class="app-wrapper">
    <!-- 侧边栏 -->
    <div :class="['sidebar-container', { collapsed: appStore.sidebarCollapsed }]">
      <div class="sidebar-logo">
        <img src="/vite.svg" alt="logo" v-if="!appStore.sidebarCollapsed" />
        <span v-show="!appStore.sidebarCollapsed">ARMS 管理系统</span>
        <span v-show="appStore.sidebarCollapsed" style="font-size:14px">AR</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>首页仪表盘</template>
        </el-menu-item>

        <el-menu-item index="/customer" v-if="checkPerm('customer')">
          <el-icon><User /></el-icon>
          <template #title>客户管理</template>
        </el-menu-item>

        <el-menu-item index="/contract" v-if="checkPerm('contract')">
          <el-icon><Document /></el-icon>
          <template #title>合同管理</template>
        </el-menu-item>

        <el-sub-menu index="finance" v-if="checkPerm('payment') || checkPerm('invoice')">
          <template #title>
            <el-icon><Coin /></el-icon>
            <span>财务管理</span>
          </template>
          <el-menu-item index="/finance/payment" v-if="checkPerm('payment')">回款管理</el-menu-item>
          <el-menu-item index="/finance/invoice" v-if="checkPerm('invoice')">开票管理</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/collection" v-if="checkPerm('collection')">
          <el-icon><Bell /></el-icon>
          <template #title>催款管理</template>
        </el-menu-item>

        <el-sub-menu index="limitation-group" v-if="checkPerm('limitation:view') || checkPerm('limitation')">
          <template #title>
            <el-icon><Timer /></el-icon>
            <span>时效管理</span>
          </template>
          <el-menu-item index="/limitation" v-if="checkPerm('limitation:view')">时效看板</el-menu-item>
          <el-menu-item index="/limitation/list" v-if="checkPerm('limitation')">时效列表</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/progress" v-if="checkPerm('progress')">
          <el-icon><TrendCharts /></el-icon>
          <template #title>付款进度</template>
        </el-menu-item>

        <el-menu-item index="/report" v-if="checkPerm('report')">
          <el-icon><PieChart /></el-icon>
          <template #title>报表中心</template>
        </el-menu-item>

        <el-sub-menu index="system" v-if="checkPerm('system:user') || checkPerm('system:role') || checkPerm('system:log') || checkPerm('system:config')">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system/user" v-if="checkPerm('system:user')">用户管理</el-menu-item>
          <el-menu-item index="/system/role" v-if="checkPerm('system:role')">角色管理</el-menu-item>
          <el-menu-item index="/system/log" v-if="checkPerm('system:log')">操作日志</el-menu-item>
          <el-menu-item index="/system/config" v-if="checkPerm('system:config')">系统配置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>

    <!-- 右侧主内容区 -->
    <div class="main-container" @click="handleMobileSidebar">
      <!-- 顶部导航栏 -->
      <div class="navbar">
        <div class="navbar-left">
          <el-icon class="hamburger" @click.stop="appStore.toggleSidebar()">
            <Fold v-if="!appStore.sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb class="breadcrumb" separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRouteTitle">{{ currentRouteTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="navbar-right">
          <el-dropdown trigger="click">
            <div class="el-dropdown-link">
              <el-avatar :size="32" :icon="UserFilled" />
              <span style="margin-left:8px;">{{ userStore.userInfo?.username || '管理员' }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="showPasswordDialog = true">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive :include="['Dashboard', 'Customer', 'Contract', 'LimitationDashboard']">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </div>
    </div>

    <!-- 遮罩层（移动端） -->
    <div
      v-if="mobileSidebarVisible"
      class="mobile-sidebar-mask"
      @click="handleMobileSidebar"
    />

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showPasswordDialog" title="修改密码" width="450px">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px" class="dialog-form">
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="passwordLoading">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { changePassword } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const showPasswordDialog = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)
const mobileSidebarVisible = ref(false)

const activeMenu = computed(() => route.path)
const currentRouteTitle = computed(() => route.meta?.title || '')

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (_rule, value, callback) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

function checkPerm(permCode) {
  const result = userStore.hasPermission(permCode)
  console.log('checkPerm', permCode, '->', result, '| userInfo:', userStore.userInfo, '| permissions:', userStore.permissions)
  return result
}

function handleMobileSidebar() {
  if (window.innerWidth <= 768 && !appStore.sidebarCollapsed) {
    appStore.setSidebarCollapsed(true)
  }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await userStore.logoutAction()
    router.push('/login')
    ElMessage.success('已退出登录')
  }).catch(() => {})
}

async function handleChangePassword() {
  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }
  passwordLoading.value = true
  try {
    await changePassword(passwordForm.value)
    ElMessage.success('密码修改成功')
    showPasswordDialog.value = false
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  } catch {
    // error handled by interceptor
  } finally {
    passwordLoading.value = false
  }
}

// 响应式处理
function handleResize() {
  if (window.innerWidth <= 768) {
    appStore.setSidebarCollapsed(true)
  }
}

watch(() => appStore.sidebarCollapsed, (val) => {
  if (window.innerWidth <= 768) {
    mobileSidebarVisible.value = !val
  }
})

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.mobile-sidebar-mask {
  display: none;
}
@media screen and (max-width: 768px) {
  .mobile-sidebar-mask {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
  }
}
</style>