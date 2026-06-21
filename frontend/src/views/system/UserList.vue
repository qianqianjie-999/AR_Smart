<template>
  <div class="user-container">
    <h2 class="page-title">用户管理</h2>

    <el-form :inline="true" :model="searchForm" class="search-bar">
      <el-form-item label="用户名"><el-input v-model="searchForm.username" placeholder="搜索用户名" clearable /></el-form-item>
      <el-form-item label="状态">
        <el-select v-model="searchForm.status" placeholder="全部" clearable style="width:120px">
          <el-option label="启用" :value="1" /><el-option label="禁用" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadList"><el-icon><Search /></el-icon> 搜索</el-button>
        <el-button type="success" @click="openDialog(null)"><el-icon><Plus /></el-icon> 新增用户</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="tableData" border stripe v-loading="loading">
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="real_name" label="姓名" />
      <el-table-column prop="phone" label="手机号" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="dept" label="部门" />
      <el-table-column label="角色">
        <template #default="{row}">
          <el-tag size="small">{{ row.role_name || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-switch :model-value="row.status === 1" @change="(v) => toggleStatus(row, v)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{row}">
          <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="total, prev, pager, next" @current-change="loadList"
      style="margin-top:16px;justify-content:flex-end"
    />

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="500px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="密码" :prop="form.id ? '' : 'password'">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.id ? '不修改请留空' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="部门"><el-input v-model="form.dept" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" placeholder="请选择角色" style="width:100%">
            <el-option v-for="r in roleList" :key="r.id" :label="r.role_name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, createUser, updateUser, deleteUser } from '@/api/system'
import { getRoleList } from '@/api/system'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchForm = reactive({ username: '', status: null })

const dialogVisible = ref(false)
const dialogTitle = computed(() => form.id ? '编辑用户' : '新增用户')
const formRef = ref(null)
const submitting = ref(false)
const roleList = ref([])

const form = reactive({
  id: null, username: '', password: '', real_name: '', phone: '', email: '',
  dept: '', role_id: null, status: 1
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

async function loadList() {
  loading.value = true
  try {
    const res = await getUserList({ page: page.value, pageSize: pageSize.value, ...searchForm })
    tableData.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (e) { /* ignore */ }
  loading.value = false
}

async function loadRoles() {
  const res = await getRoleList()
  roleList.value = res.data?.list || res.data || []
}

function openDialog(row) {
  if (row) {
    Object.assign(form, { ...row, password: '' })
  } else {
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(form, { id: null, username: '', password: '', real_name: '', phone: '', email: '', dept: '', role_id: null, status: 1 })
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitting.value = true
  try {
    if (form.id) {
      await updateUser(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createUser({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch (e) { /* ignore */ }
  submitting.value = false
}

async function toggleStatus(row, v) {
  try {
    await updateUser(row.id, { status: v ? 1 : 0 })
    row.status = v ? 1 : 0
    ElMessage.success(v ? '已启用' : '已禁用')
  } catch (e) { /* ignore */ }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '确认', { type: 'warning' })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch { /* cancelled */ }
}

onMounted(() => {
  loadList()
  loadRoles()
})
</script>
