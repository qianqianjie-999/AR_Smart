-- ============================================
-- 企业应收账款管理系统（ARMS）数据库初始化脚本
-- 兼容 MariaDB 10.11+ / MySQL 8.0+
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS arms_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE arms_db;

-- ============================================
-- 1. 客户表
-- ============================================
DROP TABLE IF EXISTS customer_contact;
DROP TABLE IF EXISTS payment_record;
DROP TABLE IF EXISTS invoice_record;
DROP TABLE IF EXISTS collection_record;
DROP TABLE IF EXISTS limitation_record;
DROP TABLE IF EXISTS notification_record;
DROP TABLE IF EXISTS payment_node;
DROP TABLE IF EXISTS contract;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS operation_log;
DROP TABLE IF EXISTS sys_role_permission;
DROP TABLE IF EXISTS sys_permission;
DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_role;
DROP TABLE IF EXISTS sys_config;

CREATE TABLE sys_config (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    config_key  VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '配置说明',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

CREATE TABLE sys_role (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    role_name   VARCHAR(50) NOT NULL COMMENT '角色名称',
    role_code   VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
    description TEXT COMMENT '角色描述',
    is_system   TINYINT DEFAULT 0 COMMENT '是否系统内置角色 1是 0否',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

CREATE TABLE sys_user (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    username    VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名',
    password    VARCHAR(255) NOT NULL COMMENT '密码（bcrypt加密）',
    real_name   VARCHAR(100) COMMENT '真实姓名',
    phone       VARCHAR(50) COMMENT '手机号',
    email       VARCHAR(100) COMMENT '邮箱',
    avatar      VARCHAR(500) COMMENT '头像URL',
    dept        VARCHAR(100) COMMENT '部门',
    role_id     BIGINT COMMENT '角色ID',
    status      TINYINT DEFAULT 1 COMMENT '状态 1启用 0禁用',
    last_login  DATETIME COMMENT '最后登录时间',
    login_ip    VARCHAR(50) COMMENT '最后登录IP',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

CREATE TABLE sys_permission (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    perm_name   VARCHAR(100) NOT NULL COMMENT '权限名称',
    perm_code   VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码',
    perm_type   VARCHAR(20) COMMENT '权限类型：menu/button/api',
    parent_id   BIGINT DEFAULT 0 COMMENT '父权限ID',
    module      VARCHAR(50) COMMENT '所属模块',
    path        VARCHAR(200) COMMENT '路由路径/API路径',
    icon        VARCHAR(100) COMMENT '菜单图标',
    sort_order  INT DEFAULT 0 COMMENT '排序',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

CREATE TABLE sys_role_permission (
    role_id     BIGINT NOT NULL COMMENT '角色ID',
    perm_id     BIGINT NOT NULL COMMENT '权限ID',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, perm_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

CREATE TABLE customer (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    region          VARCHAR(50) NOT NULL COMMENT '区域',
    name            VARCHAR(200) NOT NULL COMMENT '客户名称',
    registered_addr VARCHAR(500) COMMENT '客户注册地址',
    contact_addr    VARCHAR(500) COMMENT '客户联系地址',
    billing_info    TEXT COMMENT '开票信息（JSON格式）',
    business_contact VARCHAR(100) COMMENT '业务联系人姓名',
    credit_level    VARCHAR(20) DEFAULT 'B' COMMENT '信用等级 A/B/C/D',
    remark          TEXT COMMENT '备注',
    is_deleted      TINYINT DEFAULT 0 COMMENT '是否删除 0否 1是',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by      BIGINT COMMENT '创建人ID',
    updated_by      BIGINT COMMENT '更新人ID',
    INDEX idx_region (region),
    INDEX idx_name (name),
    INDEX idx_credit (credit_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户表';

CREATE TABLE customer_contact (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    customer_id     BIGINT NOT NULL COMMENT '关联客户ID',
    contact_type    VARCHAR(20) NOT NULL COMMENT '联系人类型：第一/第二/第三/其他',
    name            VARCHAR(100) COMMENT '联系人姓名',
    phone           VARCHAR(50) COMMENT '联系电话',
    email           VARCHAR(100) COMMENT '邮箱',
    position        VARCHAR(100) COMMENT '职位',
    is_primary      TINYINT DEFAULT 0 COMMENT '是否主要联系人 1是 0否',
    remark          VARCHAR(500) COMMENT '备注',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE,
    INDEX idx_customer (customer_id),
    INDEX idx_type (contact_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户联系人表';

CREATE TABLE contract (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    customer_id         BIGINT NOT NULL COMMENT '关联客户ID',
    contract_no         VARCHAR(100) COMMENT '合同编号',
    project_name        VARCHAR(500) NOT NULL COMMENT '项目名称',
    sign_date           DATE COMMENT '签订日期',
    acceptance_date     DATE COMMENT '验收日期',
    contract_amount     DECIMAL(18,2) DEFAULT 0 COMMENT '合同金额（元）',
    audit_amount        DECIMAL(18,2) DEFAULT 0 COMMENT '审计（结算）金额（元）',
    payment_method      TEXT COMMENT '付款方式说明',
    payment_terms       TEXT COMMENT '付款节点描述',
    status              VARCHAR(20) DEFAULT '执行中' COMMENT '状态：执行中/已完成/已终止',
    total_paid          DECIMAL(18,2) DEFAULT 0 COMMENT '累计回款金额（元）',
    outstanding_amount  DECIMAL(18,2) DEFAULT 0 COMMENT '尚欠金额（元）',
    current_due_amount  DECIMAL(18,2) DEFAULT 0 COMMENT '当前到期应收款（元）',
    total_invoiced      DECIMAL(18,2) DEFAULT 0 COMMENT '累计开票金额（元）',
    contract_file       VARCHAR(500) COMMENT '合同附件路径',
    acceptance_file     VARCHAR(500) COMMENT '验收资料附件路径',
    settlement_file     VARCHAR(500) COMMENT '结算附件路径',
    is_deleted          TINYINT DEFAULT 0 COMMENT '是否删除 0否 1是',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by          BIGINT COMMENT '创建人ID',
    updated_by          BIGINT COMMENT '更新人ID',
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    INDEX idx_customer (customer_id),
    INDEX idx_status (status),
    INDEX idx_sign_date (sign_date),
    INDEX idx_project_name (project_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同表';

CREATE TABLE payment_node (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    contract_id     BIGINT NOT NULL COMMENT '关联合同ID',
    node_no         INT NOT NULL COMMENT '节点序号',
    node_name       VARCHAR(200) COMMENT '节点名称',
    pay_ratio       DECIMAL(5,2) COMMENT '付款比例（%）',
    pay_amount      DECIMAL(18,2) COMMENT '应付金额（元）',
    due_date        DATE COMMENT '应付时间',
    due_condition   TEXT COMMENT '付款条件',
    actual_pay_date DATE COMMENT '实际付款日期',
    actual_pay_amount DECIMAL(18,2) DEFAULT 0 COMMENT '实际付款金额（元）',
    status          VARCHAR(20) DEFAULT '未到期' COMMENT '状态：未到期/已到期/已付款/逾期',
    remark          TEXT COMMENT '备注',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contract(id) ON DELETE CASCADE,
    INDEX idx_contract (contract_id),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='付款节点表';

CREATE TABLE payment_record (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    contract_id     BIGINT NOT NULL COMMENT '关联合同ID',
    payment_no      INT COMMENT '回款次数',
    amount          DECIMAL(18,2) NOT NULL COMMENT '回款金额（元）',
    payment_date    DATE COMMENT '回款时间',
    payment_method  VARCHAR(50) COMMENT '回款方式：银行转账/银行承兑/现金/其他',
    bank_account    VARCHAR(100) COMMENT '回款银行账号',
    remark          TEXT COMMENT '备注',
    interrupt_limitation TINYINT DEFAULT 1 COMMENT '是否中断时效 1是 0否',
    is_deleted      TINYINT DEFAULT 0 COMMENT '是否删除 0否 1是',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by      BIGINT COMMENT '登记人ID',
    updated_by      BIGINT COMMENT '更新人ID',
    FOREIGN KEY (contract_id) REFERENCES contract(id) ON DELETE CASCADE,
    INDEX idx_contract (contract_id),
    INDEX idx_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回款记录表';

CREATE TABLE invoice_record (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    contract_id     BIGINT NOT NULL COMMENT '关联合同ID',
    invoice_no      VARCHAR(100) COMMENT '发票号码',
    amount          DECIMAL(18,2) NOT NULL COMMENT '开票金额（元）',
    invoice_date    DATE COMMENT '开票时间',
    invoice_type    VARCHAR(50) COMMENT '发票类型',
    invoice_file    VARCHAR(500) COMMENT '发票附件路径',
    remark          TEXT COMMENT '备注',
    is_deleted      TINYINT DEFAULT 0 COMMENT '是否删除 0否 1是',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by      BIGINT COMMENT '登记人ID',
    FOREIGN KEY (contract_id) REFERENCES contract(id) ON DELETE CASCADE,
    INDEX idx_contract (contract_id),
    INDEX idx_date (invoice_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='开票记录表';

CREATE TABLE collection_record (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    contract_id         BIGINT NOT NULL COMMENT '关联合同ID',
    collection_date     DATE COMMENT '催款函发送时间',
    collection_type     VARCHAR(50) COMMENT '催款方式：EMS/电子邮件/上门催收/电话催收/律师函/其他',
    collection_content  TEXT COMMENT '催款内容',
    express_no          VARCHAR(100) COMMENT '快递单号（EMS）',
    recipient           VARCHAR(100) COMMENT '收件人',
    sign_status         VARCHAR(20) COMMENT '签收状态：已签收/未签收/退回/待查询',
    collection_file     VARCHAR(500) COMMENT '催款函附件路径',
    is_limitation_interrupt TINYINT DEFAULT 1 COMMENT '是否中断时效 1是 0否',
    remark              TEXT COMMENT '备注',
    is_deleted          TINYINT DEFAULT 0 COMMENT '是否删除 0否 1是',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by          BIGINT COMMENT '操作人ID',
    FOREIGN KEY (contract_id) REFERENCES contract(id) ON DELETE CASCADE,
    INDEX idx_contract (contract_id),
    INDEX idx_date (collection_date),
    INDEX idx_type (collection_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='催款记录表';

CREATE TABLE limitation_record (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    contract_id         BIGINT NOT NULL COMMENT '关联合同ID',
    base_date           DATE COMMENT '基准日期',
    base_type           VARCHAR(50) COMMENT '基准类型',
    limitation_end_date DATE COMMENT '时效到期日',
    days_remaining      INT COMMENT '剩余天数',
    status              VARCHAR(20) DEFAULT '有效' COMMENT '时效状态：有效/即将到期/已过期',
    interrupt_event     VARCHAR(500) COMMENT '中断时效事件描述',
    interrupt_date      DATE COMMENT '中断时效日期',
    interrupt_type      VARCHAR(50) COMMENT '中断类型：回款/催款/诉讼/对账/其他',
    next_limitation_end DATE COMMENT '重新计算后的时效到期日',
    warning_90_sent     TINYINT DEFAULT 0 COMMENT '90天预警是否已发送',
    warning_30_sent     TINYINT DEFAULT 0 COMMENT '30天预警是否已发送',
    warning_7_sent      TINYINT DEFAULT 0 COMMENT '7天预警是否已发送',
    expired_notice_sent TINYINT DEFAULT 0 COMMENT '过期通知是否已发送',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contract(id) ON DELETE CASCADE,
    INDEX idx_contract (contract_id),
    INDEX idx_end_date (limitation_end_date),
    INDEX idx_status (status),
    INDEX idx_days (days_remaining)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='诉讼时效记录表';

CREATE TABLE notification_record (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    contract_id     BIGINT NOT NULL COMMENT '关联合同ID',
    limitation_id   BIGINT COMMENT '关联时效记录ID',
    notify_type     VARCHAR(20) COMMENT '通知类型：90天预警/30天预警/7天预警/已过期',
    notify_method   VARCHAR(50) COMMENT '通知方式：系统通知/邮件/短信/钉钉',
    notify_content  TEXT COMMENT '通知内容',
    notify_status   VARCHAR(20) DEFAULT '待发送' COMMENT '状态：待发送/已发送/发送失败',
    sent_at         DATETIME COMMENT '发送时间',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contract (contract_id),
    INDEX idx_type (notify_type),
    INDEX idx_status (notify_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警通知记录表';

CREATE TABLE operation_log (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id     BIGINT COMMENT '操作用户ID',
    username    VARCHAR(100) COMMENT '用户名',
    module      VARCHAR(50) COMMENT '操作模块',
    action      VARCHAR(50) COMMENT '操作类型',
    content     TEXT COMMENT '操作内容（JSON格式）',
    ip_address  VARCHAR(50) COMMENT 'IP地址',
    user_agent  VARCHAR(500) COMMENT '浏览器信息',
    duration    INT COMMENT '执行时长（毫秒）',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_module (module),
    INDEX idx_action (action),
    INDEX idx_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================
-- 初始化数据
-- ============================================

-- 系统配置
INSERT INTO sys_config (config_key, config_value, description) VALUES
('limitation_warning_90', '90', '时效预警提前天数：90天'),
('limitation_warning_30', '30', '时效预警提前天数：30天'),
('limitation_warning_7', '7', '时效预警提前天数：7天'),
('page_size_default', '20', '默认分页大小'),
('file_max_size', '52428800', '上传文件最大大小（字节）：50MB'),
('backup_retention_days', '30', '备份保留天数');

-- 角色
INSERT INTO sys_role (id, role_name, role_code, description, is_system) VALUES
(1, '系统管理员', 'admin', '系统最高权限，可管理所有功能', 1),
(2, '财务人员', 'finance', '负责回款登记、开票管理、账龄分析', 1),
(3, '业务人员', 'business', '负责合同录入、客户维护、催款跟进', 1),
(4, '法务人员', 'legal', '负责时效监控、催款函管理、诉讼跟踪', 1),
(5, '部门经理', 'manager', '数据查看、审批、报表分析', 1),
(6, '普通查看', 'viewer', '仅查看数据，无操作权限', 1);

-- 默认管理员（密码 admin123，bcrypt加密）
INSERT INTO sys_user (username, password, real_name, role_id, status)
VALUES ('admin', '$2b$12$LJ3m4ys3Lk0TSwHCpNqrGO8rYkCvKwN/WAVGFHcxdSXJGR4AxzQqu', '系统管理员', 1, 1);

-- 权限
INSERT INTO sys_permission (id, perm_name, perm_code, perm_type, module, path, icon, sort_order) VALUES
(1, '客户管理', 'customer', 'menu', '客户管理', '/customer', 'user', 1),
(2, '客户查看', 'customer:view', 'button', '客户管理', '', '', 10),
(3, '客户新增', 'customer:create', 'button', '客户管理', '', '', 20),
(4, '客户编辑', 'customer:update', 'button', '客户管理', '', '', 30),
(5, '客户删除', 'customer:delete', 'button', '客户管理', '', '', 40),
(6, '客户导出', 'customer:export', 'button', '客户管理', '', '', 50),
(7, '合同管理', 'contract', 'menu', '合同管理', '/contract', 'document', 2),
(8, '合同查看', 'contract:view', 'button', '合同管理', '', '', 10),
(9, '合同新增', 'contract:create', 'button', '合同管理', '', '', 20),
(10, '合同编辑', 'contract:update', 'button', '合同管理', '', '', 30),
(11, '合同删除', 'contract:delete', 'button', '合同管理', '', '', 40),
(12, '合同导出', 'contract:export', 'button', '合同管理', '', '', 50),
(13, '回款管理', 'payment', 'menu', '财务管理', '/finance/payment', 'money', 3),
(14, '回款查看', 'payment:view', 'button', '财务管理', '', '', 10),
(15, '回款登记', 'payment:create', 'button', '财务管理', '', '', 20),
(16, '回款编辑', 'payment:update', 'button', '财务管理', '', '', 30),
(17, '回款删除', 'payment:delete', 'button', '财务管理', '', '', 40),
(18, '开票管理', 'invoice', 'menu', '财务管理', '/finance/invoice', 'ticket', 4),
(19, '开票查看', 'invoice:view', 'button', '财务管理', '', '', 10),
(20, '开票登记', 'invoice:create', 'button', '财务管理', '', '', 20),
(21, '开票编辑', 'invoice:update', 'button', '财务管理', '', '', 30),
(22, '开票删除', 'invoice:delete', 'button', '财务管理', '', '', 40),
(23, '催款管理', 'collection', 'menu', '催款管理', '/collection', 'message', 5),
(24, '催款查看', 'collection:view', 'button', '催款管理', '', '', 10),
(25, '催款登记', 'collection:create', 'button', '催款管理', '', '', 20),
(26, '催款编辑', 'collection:update', 'button', '催款管理', '', '', 30),
(27, '催款删除', 'collection:delete', 'button', '催款管理', '', '', 40),
(28, '时效管理', 'limitation', 'menu', '时效管理', '/limitation', 'alarm-clock', 6),
(29, '时效查看', 'limitation:view', 'button', '时效管理', '', '', 10),
(30, '时效中断', 'limitation:interrupt', 'button', '时效管理', '', '', 20),
(31, '付款进度', 'progress', 'menu', '付款进度', '/progress', 'trend-charts', 7),
(32, '进度查看', 'progress:view', 'button', '付款进度', '', '', 10),
(33, '报表中心', 'report', 'menu', '报表中心', '/report', 'pie-chart', 8),
(34, '报表查看', 'report:view', 'button', '报表中心', '', '', 10),
(35, '报表导出', 'report:export', 'button', '报表中心', '', '', 20),
(36, '系统管理', 'system', 'menu', '系统管理', '/system', 'setting', 9),
(37, '用户管理', 'system:user', 'button', '系统管理', '', '', 10),
(38, '角色管理', 'system:role', 'button', '系统管理', '', '', 20),
(39, '权限管理', 'system:permission', 'button', '系统管理', '', '', 30),
(40, '操作日志', 'system:log', 'button', '系统管理', '', '', 40),
(41, '系统配置', 'system:config', 'button', '系统管理', '', '', 50);

-- 管理员拥有所有权限
INSERT INTO sys_role_permission (role_id, perm_id)
SELECT 1, id FROM sys_permission;

-- 基本权限分配
INSERT INTO sys_role_permission (role_id, perm_id) VALUES
(2, 1),(2, 2),(2, 6), -- 财务：客户查看+导出
(2, 7),(2, 8),(2, 12), -- 合同查看+导出
(2, 13),(2, 14),(2, 15),(2, 16),(2, 17), -- 回款全权限
(2, 18),(2, 19),(2, 20),(2, 21),(2, 22), -- 开票全权限
(2, 28),(2, 29), -- 时效查看
(2, 31),(2, 32), -- 进度查看
(2, 33),(2, 34),(2, 35); -- 报表

INSERT INTO sys_role_permission (role_id, perm_id) VALUES
(3, 1),(3, 2),(3, 3),(3, 4),(3, 6), -- 客户
(3, 7),(3, 8),(3, 9),(3, 10),(3, 12), -- 合同
(3, 13),(3, 14), -- 回款查看
(3, 18),(3, 19), -- 开票查看
(3, 23),(3, 24),(3, 25),(3, 26), -- 催款
(3, 28),(3, 29), -- 时效查看
(3, 31),(3, 32), -- 进度
(3, 33),(3, 34),(3, 35); -- 报表

INSERT INTO sys_role_permission (role_id, perm_id) VALUES
(4, 1),(4, 2), -- 客户查看
(4, 7),(4, 8), -- 合同查看
(4, 23),(4, 24),(4, 25),(4, 26), -- 催款
(4, 28),(4, 29),(4, 30), -- 时效全权限
(4, 31),(4, 32), -- 进度
(4, 33),(4, 34),(4, 35); -- 报表

INSERT INTO sys_role_permission (role_id, perm_id) VALUES
(5, 1),(5, 2),(5, 6), -- 客户
(5, 7),(5, 8),(5, 12), -- 合同
(5, 13),(5, 14), -- 回款查看
(5, 18),(5, 19), -- 开票查看
(5, 23),(5, 24), -- 催款查看
(5, 28),(5, 29), -- 时效查看
(5, 31),(5, 32), -- 进度
(5, 33),(5, 34),(5, 35); -- 报表

INSERT INTO sys_role_permission (role_id, perm_id) VALUES
(6, 1),(6, 2), -- 客户查看
(6, 7),(6, 8), -- 合同查看
(6, 13),(6, 14), -- 回款查看
(6, 18),(6, 19), -- 开票查看
(6, 23),(6, 24), -- 催款查看
(6, 28),(6, 29), -- 时效查看
(6, 31),(6, 32), -- 进度
(6, 33),(6, 34); -- 报表查看

SET FOREIGN_KEY_CHECKS = 1;
