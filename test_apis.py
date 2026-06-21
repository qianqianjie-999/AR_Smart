"""
前后端 API 接口测试脚本
测试所有模块的 API 接口是否正常工作
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, success, message=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if success else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} - {name}")
    if message and not success:
        print(f"       {Colors.RED}{message}{Colors.RESET}")

def get_token():
    """登录获取token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    data = resp.json()
    if data.get('code') == 200:
        return data['data']['token']
    return None

def test_auth():
    """测试认证模块"""
    print(f"\n{Colors.BLUE}=== 认证模块 ==={Colors.RESET}")

    # 登录
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    print_test("登录", resp.json().get('code') == 200)

    token = resp.json()['data']['token']
    headers = {"Authorization": f"Bearer {token}"}

    # 获取用户信息
    resp = requests.get(f"{BASE_URL}/auth/userinfo", headers=headers)
    data = resp.json()
    print_test("获取用户信息", data.get('code') == 200 and len(data['data']['permissions']) > 0)

    return token, headers

def test_customer(headers):
    """测试客户管理模块"""
    print(f"\n{Colors.BLUE}=== 客户管理模块 ==={Colors.RESET}")

    # 客户列表
    resp = requests.get(f"{BASE_URL}/customer/", headers=headers)
    print_test("客户列表", resp.json().get('code') == 200)

    # 创建客户
    resp = requests.post(f"{BASE_URL}/customer/", headers=headers, json={
        "name": "测试客户公司",
        "contact_name": "张三",
        "contact_phone": "13800138000",
        "region": "华东"
    })
    cid = None
    if resp.json().get('code') == 200:
        cid = resp.json()['data'].get('id')
        print_test("创建客户", True)
    else:
        print_test("创建客户", False, resp.json().get('message'))

    # 更新客户
    if cid:
        resp = requests.put(f"{BASE_URL}/customer/{cid}", headers=headers, json={
            "name": "测试客户公司(已修改)",
            "contact_name": "李四"
        })
        print_test("更新客户", resp.json().get('code') == 200)

    return cid

def test_contract(headers, customer_id):
    """测试合同管理模块"""
    print(f"\n{Colors.BLUE}=== 合同管理模块 ==={Colors.RESET}")

    # 创建合同
    resp = requests.post(f"{BASE_URL}/contract/", headers=headers, json={
        "customer_id": customer_id,
        "project_name": "测试合同项目",
        "contract_amount": 500000,
        "sign_date": "2024-01-15",
        "status": "执行中"
    })
    cid = None
    if resp.json().get('code') == 200:
        cid = resp.json()['data'].get('id')
        print_test("创建合同", True)
    else:
        print_test("创建合同", False, resp.json().get('message'))

    # 合同列表
    resp = requests.get(f"{BASE_URL}/contract/", headers=headers)
    print_test("合同列表", resp.json().get('code') == 200)

    # 合同详情
    if cid:
        resp = requests.get(f"{BASE_URL}/contract/{cid}", headers=headers)
        print_test("合同详情", resp.json().get('code') == 200)

    # 更新合同
    if cid:
        resp = requests.put(f"{BASE_URL}/contract/{cid}", headers=headers, json={
            "project_name": "测试合同项目(已修改)",
            "contract_amount": 600000
        })
        print_test("更新合同", resp.json().get('code') == 200)

    return cid

def test_payment(headers, contract_id):
    """测试回款管理模块"""
    print(f"\n{Colors.BLUE}=== 回款管理模块 ==={Colors.RESET}")

    # 创建回款记录
    resp = requests.post(f"{BASE_URL}/payment/", headers=headers, json={
        "contract_id": contract_id,
        "amount": 100000,
        "payment_date": "2024-02-01",
        "payment_method": "银行转账",
        "status": "已确认"
    })
    pid = None
    if resp.json().get('code') == 200:
        pid = resp.json()['data'].get('id')
        print_test("创建回款记录", True)
    else:
        print_test("创建回款记录", False, resp.json().get('message'))

    # 回款列表
    resp = requests.get(f"{BASE_URL}/payment/", headers=headers)
    print_test("回款列表", resp.json().get('code') == 200)

    return pid

def test_invoice(headers, contract_id):
    """测试开票管理模块"""
    print(f"\n{Colors.BLUE}=== 开票管理模块 ==={Colors.RESET}")

    # 创建开票记录
    resp = requests.post(f"{BASE_URL}/invoice/", headers=headers, json={
        "contract_id": contract_id,
        "invoice_no": "FP20240201001",
        "amount": 50000,
        "invoice_date": "2024-02-01",
        "invoice_type": "增值税专用发票",
        "tax_rate": 0.13,
        "status": "已开票"
    })
    iid = None
    if resp.json().get('code') == 200:
        iid = resp.json()['data'].get('id')
        print_test("创建开票记录", True)
    else:
        print_test("创建开票记录", False, resp.json().get('message'))

    # 上传发票附件
    if iid:
        resp = requests.post(f"{BASE_URL}/invoice/{iid}/upload", headers=headers, json={
            "invoice_file": "/uploads/invoice/test.pdf"
        })
        print_test("上传发票附件", resp.json().get('code') == 200)

    # 开票列表
    resp = requests.get(f"{BASE_URL}/invoice/", headers=headers)
    print_test("开票列表", resp.json().get('code') == 200)

    return iid

def test_collection(headers, contract_id):
    """测试催款管理模块"""
    print(f"\n{Colors.BLUE}=== 催款管理模块 ==={Colors.RESET}")

    # 创建催款记录
    resp = requests.post(f"{BASE_URL}/collection/", headers=headers, json={
        "contract_id": contract_id,
        "collection_type": "电话催款",
        "collection_date": "2024-02-15",
        "amount": 200000,
        "response": "同意近期付款",
        "status": "跟进中"
    })
    cid = None
    if resp.json().get('code') == 200:
        cid = resp.json()['data'].get('id')
        print_test("创建催款记录", True)
    else:
        print_test("创建催款记录", False, resp.json().get('message'))

    # 上传催款函附件
    if cid:
        resp = requests.post(f"{BASE_URL}/collection/{cid}/upload", headers=headers, json={
            "collection_file": "/uploads/collection/test.pdf"
        })
        print_test("上传催款函附件", resp.json().get('code') == 200)

    # 催款列表
    resp = requests.get(f"{BASE_URL}/collection/", headers=headers)
    print_test("催款列表", resp.json().get('code') == 200)

    return cid

def test_limitation(headers, contract_id):
    """测试时效管理模块"""
    print(f"\n{Colors.BLUE}=== 时效管理模块 ==={Colors.RESET}")

    # 时效列表
    resp = requests.get(f"{BASE_URL}/limitation/", headers=headers)
    print_test("时效列表", resp.json().get('code') == 200)

    # 时效看板
    resp = requests.get(f"{BASE_URL}/limitation/dashboard", headers=headers)
    print_test("时效看板", resp.json().get('code') == 200)

    # 时效历史 - 后端路由是 /<int:id>/history (id是时效记录ID)
    resp = requests.get(f"{BASE_URL}/limitation/", headers=headers)
    if resp.json().get('code') == 200 and resp.json()['data']['total'] > 0:
        lid = resp.json()['data']['list'][0]['id']
        resp = requests.get(f"{BASE_URL}/limitation/{lid}/history", headers=headers)
        print_test("时效历史", resp.json().get('code') == 200)
    else:
        print_test("时效历史", True, "无时效记录，跳过")

    return None

def test_report(headers):
    """测试报表模块"""
    print(f"\n{Colors.BLUE}=== 报表模块 ==={Colors.RESET}")

    # 汇总报表
    resp = requests.get(f"{BASE_URL}/report/summary", headers=headers)
    print_test("汇总报表", resp.json().get('code') == 200)

    # 区域报表
    resp = requests.get(f"{BASE_URL}/report/regional", headers=headers)
    print_test("区域报表", resp.json().get('code') == 200)

    # 客户排名
    resp = requests.get(f"{BASE_URL}/report/customer-ranking", headers=headers)
    print_test("客户排名", resp.json().get('code') == 200)

    # 账龄分析
    resp = requests.get(f"{BASE_URL}/report/aging", headers=headers)
    print_test("账龄分析", resp.json().get('code') == 200)

    # 到期应收
    resp = requests.get(f"{BASE_URL}/report/due-receivable", headers=headers)
    print_test("到期应收", resp.json().get('code') == 200)

    # 回款趋势
    resp = requests.get(f"{BASE_URL}/report/payment-trend", headers=headers)
    print_test("回款趋势", resp.json().get('code') == 200)

    # 时效统计
    resp = requests.get(f"{BASE_URL}/report/limitation-stats", headers=headers)
    print_test("时效统计", resp.json().get('code') == 200)

    # 导出报表
    resp = requests.get(f"{BASE_URL}/report/export/summary", headers=headers)
    print_test("导出报表", resp.status_code == 200)

def test_system(headers):
    """测试系统管理模块"""
    print(f"\n{Colors.BLUE}=== 系统管理模块 ==={Colors.RESET}")

    # 用户列表
    resp = requests.get(f"{BASE_URL}/system/users", headers=headers)
    print_test("用户列表", resp.json().get('code') == 200)

    # 角色列表
    resp = requests.get(f"{BASE_URL}/system/roles", headers=headers)
    print_test("角色列表", resp.json().get('code') == 200)

    # 权限列表
    resp = requests.get(f"{BASE_URL}/system/permissions", headers=headers)
    print_test("权限列表", resp.json().get('code') == 200)

    # 操作日志
    resp = requests.get(f"{BASE_URL}/system/logs", headers=headers)
    print_test("操作日志", resp.json().get('code') == 200)

    # 系统配置
    resp = requests.get(f"{BASE_URL}/system/config", headers=headers)
    print_test("系统配置", resp.json().get('code') == 200)

    # 数据库备份
    resp = requests.get(f"{BASE_URL}/system/backup", headers=headers)
    print_test("数据库备份", resp.status_code in [200, 201])

    # 区域列表
    resp = requests.get(f"{BASE_URL}/customer/regions", headers=headers)
    print_test("区域列表", resp.json().get('code') == 200)

def main():
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  AR Smart System - API 接口测试")
    print(f"{'='*60}{Colors.RESET}")

    # 测试认证
    token, headers = test_auth()
    if not token:
        print(f"\n{Colors.RED}登录失败，终止测试{Colors.RESET}")
        return

    # 测试客户管理
    customer_id = test_customer(headers)

    # 测试合同管理
    contract_id = test_contract(headers, customer_id or 1)

    # 测试回款管理
    test_payment(headers, contract_id or 1)

    # 测试开票管理
    test_invoice(headers, contract_id or 1)

    # 测试催款管理
    test_collection(headers, contract_id or 1)

    # 测试时效管理
    test_limitation(headers, contract_id or 1)

    # 测试报表
    test_report(headers)

    # 测试系统管理
    test_system(headers)

    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  测试完成!")
    print(f"{'='*60}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
