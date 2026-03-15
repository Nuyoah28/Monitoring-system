<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>智慧小区监控系统 - App UI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="./styles.css" />
</head>
<body>
  <main class="scene">
    <section class="device">
      <!-- ===================== 1. 全局顶部栏（所有视图共享） ===================== -->
      <header class="topbar">
        <div>
          <p class="caps">Smart Estate</p> <!-- 品牌英文标识 -->
          <h1>智慧小区监控系统</h1> <!-- 系统主标题 -->
        </div>
        <button class="icon-btn" aria-label="消息通知">🔔</button> <!-- 消息通知按钮 -->
      </header>

      <!-- ===================== 2. 视图1：AI值守助手（默认激活） ===================== -->
      <!-- 核心功能：展示AI助手的核心提示、在线设备数、异常数，以及今日巡检建议 -->
      <section class="view active" data-view="agent">
        <div class="hero"> <!-- 核心提示区 -->
          <p class="hero-tag">AI AGENT</p>
          <h2>您好，值守助手已上线</h2>
          <p>实时感知小区动态，自动生成巡检建议和风险提示。</p>
          <div class="chips"> <!-- 关键数据标签 -->
            <span>在线摄像头 24</span>
            <span>异常待处理 3</span>
          </div>
        </div>

        <article class="panel"> <!-- 今日建议面板 -->
          <div class="panel-head"> <!-- 面板头部（标题+查看详情） -->
            <h3>今日建议</h3>
            <a href="#">查看详情</a>
          </div>
          <ul class="timeline"> <!-- 时间轴式建议列表 -->
            <li>
              <strong>07:20</strong> <!-- 时间 -->
              <p>西门车辆短时拥堵，建议临时开启分流引导。</p> <!-- 建议内容 -->
            </li>
            <li>
              <strong>09:45</strong>
              <p>2号楼电梯噪声峰值偏高，建议安排设备复检。</p>
            </li>
            <li>
              <strong>11:10</strong>
              <p>儿童活动区人流升高，建议增加巡逻频次。</p>
            </li>
          </ul>
        </article>
      </section>

      <!-- ===================== 3. 视图2：报警信息 ===================== -->
      <!-- 核心功能：按优先级展示各类报警信息（高/中/低），包含报警类型、位置、时间、设备 -->
      <section class="view" data-view="alarm">
        <div class="section-title"> <!-- 板块标题+筛选按钮 -->
          <h2>报警信息</h2>
          <button class="ghost">筛选</button>
        </div>

        <article class="alarm-card high"> <!-- 高优先级报警卡片 -->
          <p class="status">高优先级</p>
          <h3>周界入侵告警</h3>
          <p>东侧围栏 03 区域，检测到可疑翻越行为。</p>
          <div class="meta">12:08 · 摄像头 E-12</div> <!-- 元信息：时间+设备 -->
        </article>

        <article class="alarm-card medium"> <!-- 中优先级报警卡片 -->
          <p class="status">中优先级</p>
          <h3>烟雾浓度异常</h3>
          <p>地下车库 B2 传感器读数持续上升，建议排查。</p>
          <div class="meta">11:41 · 传感器 S-08</div>
        </article>

        <article class="alarm-card low"> <!-- 低优先级报警卡片 -->
          <p class="status">低优先级</p>
          <h3>夜间逗留提醒</h3>
          <p>5号楼后侧通道，人员停留超过阈值时长。</p>
          <div class="meta">10:56 · 摄像头 N-05</div>
        </article>
      </section>

      <!-- ===================== 4. 视图3：监控视频 ===================== -->
      <!-- 核心功能：展示各区域监控摄像头的视频入口，包含摄像头位置、画质、状态 -->
      <section class="view" data-view="video">
        <div class="section-title"> <!-- 板块标题+布局切换按钮 -->
          <h2>监控视频</h2>
          <button class="ghost">四宫格</button>
        </div>

        <div class="video-grid"> <!-- 视频网格布局 -->
          <article> <!-- 单个摄像头卡片 -->
            <div class="frame"></div> <!-- 视频播放占位框 -->
            <h3>北门主通道</h3> <!-- 摄像头位置 -->
            <p>高清 · 实时</p> <!-- 画质+状态 -->
          </article>
          <article>
            <div class="frame"></div>
            <h3>地下车库出口</h3>
            <p>高清 · 实时</p>
          </article>
          <article>
            <div class="frame"></div>
            <h3>2号楼电梯厅</h3>
            <p>流畅 · 回放中</p>
          </article>
          <article>
            <div class="frame"></div>
            <h3>儿童活动区</h3>
            <p>高清 · 实时</p>
          </article>
        </div>
      </section>

      <!-- ===================== 5. 视图4：开放词汇检测 ===================== -->
      <!-- 核心功能：管理AI监测的关键词库，支持新增词组、展示已添加词组 -->
      <section class="view" data-view="lexicon">
        <div class="section-title"> <!-- 板块标题+导入词库按钮 -->
          <h2>开放词汇检测</h2>
          <button class="ghost">导入词库</button>
        </div>

        <article class="panel"> <!-- 词库管理面板 -->
          <h3>新增监测词组</h3>
          <form class="phrase-form" onsubmit="return false;"> <!-- 新增词组表单 -->
            <input id="phraseInput" type="text" placeholder="请输入词组，例如：攀爬围栏" /> <!-- 输入框 -->
            <button id="addPhraseBtn" type="button">添加</button> <!-- 添加按钮 -->
          </form>
          <div id="phraseList" class="phrase-list"> <!-- 已添加词组列表 -->
            <span>可疑聚集</span>
            <span>强光照射</span>
            <span>快速奔跑</span>
            <span>遮挡镜头</span>
          </div>
        </article>
      </section>

      <!-- ===================== 6. 视图5：个人中心 ===================== -->
      <!-- 核心功能：展示值班人员信息、个人资料、快捷操作按钮 -->
      <section class="view" data-view="profile">
        <div class="profile-card"> <!-- 个人信息卡片 -->
          <div class="avatar">管</div> <!-- 头像占位 -->
          <div>
            <h2>张安保</h2> <!-- 姓名 -->
            <p>智慧物业 · 值班管理员</p> <!-- 职位 -->
          </div>
        </div>

        <article class="panel"> <!-- 详细个人信息面板 -->
          <h3>个人信息</h3>
          <ul class="info-list"> <!-- 信息列表（标签+值） -->
            <li><span>工号</span><strong>WY-2037</strong></li>
            <li><span>值班时段</span><strong>08:00 - 20:00</strong></li>
            <li><span>联系电话</span><strong>138-0000-3186</strong></li>
            <li><span>负责区域</span><strong>A/B 区 + 地下车库</strong></li>
          </ul>
        </article>

        <article class="panel"> <!-- 快捷操作面板 -->
          <h3>快捷操作</h3>
          <div class="actions"> <!-- 操作按钮组 -->
            <button>导出日报</button>
            <button>交班记录</button>
            <button>退出登录</button>
          </div>
        </article>
      </section>

      <!-- ===================== 7. 全局底部导航栏（切换视图） ===================== -->
      <nav class="tabbar" aria-label="底部导航栏">
        <button class="tab active" data-tab="agent">Agent</button> <!-- 切换到AI助手视图（默认激活） -->
        <button class="tab" data-tab="alarm">报警</button> <!-- 切换到报警信息视图 -->
        <button class="tab" data-tab="video">视频</button> <!-- 切换到监控视频视图 -->
        <button class="tab" data-tab="lexicon">词汇</button> <!-- 切换到词汇检测视图 -->
        <button class="tab" data-tab="profile">我的</button> <!-- 切换到个人中心视图 -->
      </nav>
    </section>
  </main>

  <script src="./app.js"></script> <!-- 交互逻辑脚本文件 -->
</body>
</html>