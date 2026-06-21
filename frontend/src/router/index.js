import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '首页仪表盘', icon: 'Odometer' }
      },
      {
        path: 'customer',
        name: 'Customer',
        component: () => import('@/views/customer/CustomerList.vue'),
        meta: { title: '客户管理', icon: 'User', perm: 'customer:list' }
      },
      {
        path: 'contract',
        name: 'Contract',
        component: () => import('@/views/contract/ContractList.vue'),
        meta: { title: '合同管理', icon: 'Document', perm: 'contract:list' }
      },
      {
        path: 'contract/:id',
        name: 'ContractDetail',
        component: () => import('@/views/contract/ContractDetail.vue'),
        meta: { title: '合同详情', icon: 'Document', hidden: true },
        props: true
      },
      {
        path: 'finance/payment',
        name: 'Payment',
        component: () => import('@/views/finance/PaymentList.vue'),
        meta: { title: '回款管理', icon: 'Money', perm: 'payment:list' }
      },
      {
        path: 'finance/invoice',
        name: 'Invoice',
        component: () => import('@/views/finance/InvoiceList.vue'),
        meta: { title: '开票管理', icon: 'Receipt', perm: 'invoice:list' }
      },
      {
        path: 'collection',
        name: 'Collection',
        component: () => import('@/views/collection/CollectionList.vue'),
        meta: { title: '催款管理', icon: 'Bell', perm: 'collection:list' }
      },
      {
        path: 'limitation',
        name: 'LimitationDashboard',
        component: () => import('@/views/limitation/LimitationDashboard.vue'),
        meta: { title: '时效看板', icon: 'Timer', perm: 'limitation:view' }
      },
      {
        path: 'limitation/list',
        name: 'LimitationList',
        component: () => import('@/views/limitation/LimitationList.vue'),
        meta: { title: '时效列表', icon: 'List', perm: 'limitation:list' }
      },
      {
        path: 'progress',
        name: 'Progress',
        component: () => import('@/views/progress/ProgressView.vue'),
        meta: { title: '付款进度', icon: 'TrendCharts', perm: 'progress:view' }
      },
      {
        path: 'report',
        name: 'Report',
        component: () => import('@/views/report/ReportView.vue'),
        meta: { title: '报表中心', icon: 'PieChart', perm: 'report:view' }
      },
      {
        path: 'system/user',
        name: 'SystemUser',
        component: () => import('@/views/system/UserList.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', perm: 'system:user:list' }
      },
      {
        path: 'system/role',
        name: 'SystemRole',
        component: () => import('@/views/system/RoleList.vue'),
        meta: { title: '角色管理', icon: 'Avatar', perm: 'system:role:list' }
      },
      {
        path: 'system/log',
        name: 'SystemLog',
        component: () => import('@/views/system/LogList.vue'),
        meta: { title: '操作日志', icon: 'Notebook', perm: 'system:log:list' }
      },
      {
        path: 'system/config',
        name: 'SystemConfig',
        component: () => import('@/views/system/ConfigView.vue'),
        meta: { title: '系统配置', icon: 'Setting', perm: 'system:config' }
      },
      {
        path: 'template',
        name: 'Template',
        component: () => import('@/views/template/TemplateList.vue'),
        meta: { title: '模板管理', icon: 'Files', perm: 'template:list' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录时跳转到登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.noAuth) {
    // 登录页不需要认证
    next()
  } else if (!token) {
    // 未登录，跳转到登录页
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
