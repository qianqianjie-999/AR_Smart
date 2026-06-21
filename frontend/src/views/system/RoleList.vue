<template>
  <div class="role-container">
    <h2 class="page-title">角色管理</h2>
    <el-button type="success" @click="openDialog(null)" style="margin-bottom:16px">
      <el-icon><Plus /></el-icon> 新增角色
    </el-button>

    <el-table :data="tableData" border stripe v-loading="loading">
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="role_name" label="角色名称" />
      <el-table-column prop="role_code" label="角色编码" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="系统内置" width="90">
        <template #default="{row}">
          <el-tag :type="row.is_system ? 'info' : ''" size="small">{{ row.is_system ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{row}">
          <el-button type="primary" link @click="openPermDialog(row)">分配权限</el-button>
          <el-button type="warning" link @click="openDialog(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)" :disabled="row.is_system">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog :title="roleForm.id ? '编辑角色' : '新增角色'" v-model="dialogVisible" width="450px">
      <el-form ref="roleFormRef" :model="roleForm" :rules="roleRules" label-width="80px">
        <el-form-item label="名称" prop="role_name">
          <el-input v-model="roleForm.role_name" />
        </el-form-item>
        <el-form-item label="编码" prop="role_code">
          <el-input v-model="roleForm.role_code" :disabled="!!roleForm.id" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 权限分配弹窗 -->
    <el-dialog :title="`分配权限 - ${permRole?.role_name || ''}`" v-model="permVisible" width="550px">
      <el-tree
        ref="permTreeRef"
        :data="permTree"
        show-checkbox
        node-key="id"
        :default-checked-keys="checkedPermIds"
        :props="{ label: 'perm_name', children: 'children' }"
        default-expand-all
      />
      <template #footer>
        <el-button @click="permVisible = false">取消</el-button>
        <el-button type="primary" @click="savePerms" :loading="permSubmitting">保存权限</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoleList, createRole, updateRole, deleteRole, getPermissionList, updateRolePermissions } from '@/api/system'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const roleFormRef = ref(null)
const submitting = ref(false)

const roleForm = reactive({ id: null, role_name: '', role_code: '', description: '' })
const roleRules = {
  role_name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  role_code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
}

const permVisible = ref(false)
const permRole = ref(null)
const permTreeRef = ref(null)
const permTree = ref([])
const checkedPermIds = ref([])
const permSubmitting = ref(false)

async function loadList() {
  loading.value = true
  try {
    const res = await getRoleList()
    tableData.value = res.data?.list || res.data || []
  } catch (e) { /* ignore */ }
  loading.value = false
}

function openDialog(row) {
  if (row) Object.assign(roleForm, row)
  else {
    roleFormRef.value?.resetFields()
    Object.assign(roleForm, { id: null, role_name: '', role_code: '', description: '' })
  }
  dialogVisible.value = true
}

async function saveRole() {
  try { await roleFormRef.value.validate() } catch { return }
  submitting.value = true
  try {
    if (roleForm.id) {
      await updateRole(roleForm.id, { ...roleForm })
    } else {
      await createRole({ ...roleForm })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadList()
  } catch (e) { /* ignore */ }
  submitting.value = false
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除角色「${row.role_name}」吗？`, '确认', { type: 'warning' })
    await deleteRole(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch { /* cancelled */ }
}

async function openPermDialog(row) {
  permRole.value = row
  try {
    const res = await getPermissionList()
    const buildTree = (list, parentId = 0) => {
      return list.filter(p => p.parent_id === parentId).map(p => ({
        ...p, children: buildTree(list, p.id)
      }))
    }
    permTree.value = buildTree(res.data || [])
    // 获取当前角色已有权限
    checkedPermIds.value = (res.data || []).filter(p => {
      // 假设后端返回的角色权限在 data 中
      return false // 实际需要根据角色ID获取已分配权限
    })
    permVisible.value = true
  } catch (e) { /* ignore */ }
}

async function savePerms() {
  const keys = permTreeRef.value?.getCheckedKeys(true) || []
  permSubmitting.value = true
  try {
    await updateRolePermissions(permRole.value.id, keys)
    ElMessage.success('权限已更新')
    permVisible.value = false
  } catch (e) { /* ignore */ }
  permSubmitting.value = false
}

onMounted(loadList)
</script>
