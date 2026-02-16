# GitHub 发布指南

## 📋 发布前准备

### 1. 检查文件清单

确保以下文件已准备好：

```
watermark-remover/
├── README.md              ✅ 项目介绍
├── LICENSE                ✅ MIT 协议
├── .gitignore            ✅ Git 忽略配置
├── requirements.txt      ✅ 依赖清单
├── build.spec            ✅ 打包配置
├── main.py               ✅ 程序入口
├── config.yaml           ✅ 配置文件
├── core/                 ✅ 核心算法
├── services/             ✅ 业务逻辑
├── gui/                  ✅ 界面代码
├── utils/                ✅ 工具模块
├── assets/               ✅ 资源文件
└── dist/                 ✅ 打包输出
    └── watermark_remover_v1.0_dist/
        ├── watermark_remover_v1.0.exe
        └── README.txt
```

### 2. 更新版本号

在以下文件中更新版本号：

- `main.py`: `app.setApplicationVersion("1.0")`
- `README.md`: 更新版本徽章和更新日志
- `gui/components/help_dialog.py`: 帮助文档中的版本信息

## 🚀 发布步骤

### 方法一：手动发布（推荐首次使用）

#### 步骤 1: 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `watermark-remover`
   - **Description**: `基于OpenCV和PyQt6的本地离线水印去除工具`
   - **Visibility**: Public（或 Private）
   - ✅ 勾选 "Add a README file"
   - ✅ 勾选 "Add .gitignore" → 选择 "Python"
   - ✅ 勾选 "Choose a license" → 选择 "MIT License"
3. 点击 "Create repository"

#### 步骤 2: 本地初始化 Git

```bash
# 在项目根目录打开终端
cd watermark_remover

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交初始版本
git commit -m "Initial commit: 水印去除工具 v1.0"

# 添加远程仓库（替换 yourusername 为你的 GitHub 用户名）
git remote add origin https://github.com/yourusername/watermark-remover.git

# 推送到 GitHub
git push -u origin main
```

#### 步骤 3: 创建 Release

1. 在 GitHub 仓库页面，点击右侧的 "Releases"
2. 点击 "Create a new release"
3. 填写发布信息：
   - **Choose a tag**: 输入 `v1.0`，点击 "Create new tag"
   - **Release title**: `水印去除工具 v1.0`
   - **Describe this release**: 
     ```markdown
     ## 水印去除工具 v1.0

     ### ✨ 新特性
     - 支持图像去水印（PNG/JPG/JPEG/WebP/BMP）
     - 支持视频去水印（MP4/AVI/MOV/FLV/MKV）
     - 多种修复算法（TELEA/NS/高级修复）
     - 可视化 ROI 选择
     - 批量处理支持
     - 内置使用帮助文档

     ### 📥 下载
     - `watermark_remover_v1.0.exe` - Windows 可执行文件（90MB）

     ### 📝 使用说明
     1. 下载 exe 文件
     2. 双击运行
     3. 参考内置帮助文档使用

     ### ⚠️ 注意
     - 需要 Windows 10/11
     - 视频处理需要安装 ffmpeg
     ```
4. 上传打包好的 exe 文件：
   - 点击 "Attach binaries by dropping them here or selecting them"
   - 选择 `dist/watermark_remover_v1.0_dist/watermark_remover_v1.0.exe`
5. ✅ 勾选 "This is a pre-release"（如果是测试版）
6. 点击 "Publish release"

---

### 方法二：使用 GitHub Actions 自动发布

#### 步骤 1: 推送代码到 GitHub

```bash
# 确保所有文件已提交
git add .
git commit -m "Prepare for release"
git push origin main
```

#### 步骤 2: 创建 Tag 触发自动构建

```bash
# 创建版本标签
git tag -a v1.0 -m "Release version 1.0"

# 推送标签到 GitHub
git push origin v1.0
```

#### 步骤 3: 等待自动构建完成

1. 在 GitHub 仓库页面，点击 "Actions" 标签
2. 查看 "Build and Release" 工作流运行状态
3. 等待构建完成（约 5-10 分钟）
4. 构建完成后，自动创建的 Release 会出现在 "Releases" 页面

---

## 📁 文件说明

### 已创建的 GitHub 相关文件

1. **README.md** - 项目主页展示内容
   - 项目介绍
   - 功能特性
   - 安装使用说明
   - 项目结构
   - 常见问题

2. **LICENSE** - MIT 开源协议
   - 允许自由使用、修改、分发
   - 保留版权声明

3. **.gitignore** - Git 忽略配置
   - Python 相关忽略规则
   - PyInstaller 输出目录
   - IDE 配置文件
   - 临时文件和日志

4. **.github/workflows/build.yml** - GitHub Actions 工作流
   - 自动构建 Windows 可执行文件
   - 自动创建 Release
   - 上传构建产物

## 🔄 后续更新

### 发布新版本

1. 更新代码和版本号
2. 重新打包：`py -3.11 -m PyInstaller build.spec`
3. 提交更改：`git add . && git commit -m "Update to v1.1"`
4. 推送代码：`git push origin main`
5. 创建新标签：`git tag -a v1.1 -m "Release version 1.1"`
6. 推送标签：`git push origin v1.1`
7. 在 GitHub Releases 页面编辑发布说明

## 🆘 常见问题

### Q: 推送时提示权限错误？

**A:** 需要配置 GitHub 身份验证：

```bash
# 使用 HTTPS（推荐）
git remote set-url origin https://github.com/yourusername/watermark-remover.git
# 推送时会提示输入用户名和密码（密码使用 Personal Access Token）

# 或使用 SSH
git remote set-url origin git@github.com:yourusername/watermark-remover.git
```

### Q: GitHub Actions 构建失败？

**A:** 检查以下几点：
1. `requirements.txt` 是否完整
2. `build.spec` 路径是否正确
3. Python 版本是否兼容（建议使用 3.11）

### Q: Release 页面没有显示 exe 文件？

**A:** 需要手动上传或使用 Actions 自动上传。检查：
1. GitHub Actions 工作流是否成功完成
2. Release 是否已发布（不是 Draft 状态）
3. 文件是否已正确附加到 Release

## 📞 获取帮助

- [GitHub 官方文档](https://docs.github.com/)
- [创建 Release 指南](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

**祝发布顺利！** 🎉
