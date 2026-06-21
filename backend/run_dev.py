
import os, sys
sys.path.insert(0, "/home/qianqianjie/AR_Smart/backend")

os.environ["FLASK_ENV"] = "development"
os.environ["SECRET_KEY"] = "arms-dev-secret-key-min-32-chars"
os.environ["JWT_SECRET_KEY"] = "arms-jwt-secret-min-32-chars!!"

# 默认使用MariaDB
os.environ["DATABASE_URL"] = os.environ.get(
    "DATABASE_URL", 
    "mysql+pymysql://root:root123@127.0.0.1:3306/arms_db"
)

from app import create_app, db
import bcrypt

app = create_app()

with app.app_context():
    db.create_all()
    
    from app.models.system import SysUser
    if not SysUser.query.filter_by(username="admin").first():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        db.session.execute(
            db.text("INSERT INTO sys_user (username, password, real_name, role_id, status) VALUES (:u, :p, :r, :rid, :s)"),
            {"u": "admin", "p": hashed, "r": "管理员", "rid": 1, "s": 1}
        )
        db.session.commit()
        print("✅ 管理员已创建")

if __name__ == "__main__":
    print("🚀 启动 Flask 后端: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
