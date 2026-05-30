 推流：
 ffmpeg -re -stream_loop -1 -i D:\projectFBX\城市智眼\Monitoring-system\ebike.mp4 -c copy -f flv rtmp://123.56.248.17:1935/live/raw


ffmpeg -re -stream_loop -1 -i D:\projectFBX\城市智眼\Monitoring-system\fall.mp4 -c copy -f flv rtmp://123.56.248.17:1935/live/raw


# 0. 先确认上传的两个新文件确实在
ls -d /opt/web-andun-staging       # 应该有这个目录
ls /tmp/prompts_andun.py           # 应该有这个文件
grep -c '社区安盾' /tmp/prompts_andun.py    # 应 ≥ 2

# 1. 备份现行智眼
mv /opt/web /opt/web.zhiyan
cp /opt/ReAct_agent/agent_core/prompts.py /opt/ReAct_agent/agent_core/prompts.py.zhiyan

# 2. 安盾就位
mv /opt/web-andun-staging /opt/web
chown -R www-data:www-data /opt/web
cp /tmp/prompts_andun.py /opt/ReAct_agent/agent_core/prompts.py

# 3. 验证替换成功
ls /opt/web/index.html                                              # 应该存在
grep -c '社区安盾' /opt/ReAct_agent/agent_core/prompts.py            # 应 ≥ 2
grep -c '社区智眼' /opt/ReAct_agent/agent_core/prompts.py            # 应 = 0

# 4. 重启 agent（关键！否则 prompts 还是旧的）
tmux ls                            # 找到 agent 那个 session 的名字
tmux attach -t <session_name>      # 进去
# 看到 Flask 在跑 → Ctrl+C 停掉
# 然后输入：
python3 agent_api.py
# 看到 "Running on http://0.0.0.0:5050"
# Ctrl+B 然后按 D，离开 tmux

# 5. 浏览器 Ctrl+F5 强制刷新 http://123.56.248.17，确认看到安盾


# 1. 还原 web
rm -rf /opt/web
mv /opt/web.zhiyan /opt/web

# 2. 还原 prompts
cp /opt/ReAct_agent/agent_core/prompts.py.zhiyan /opt/ReAct_agent/agent_core/prompts.py

# 3. 验证还原成功
grep -c '社区智眼' /opt/ReAct_agent/agent_core/prompts.py            # 应 ≥ 2

# 4. 同样进 tmux 重启 agent
tmux attach -t <session_name>
# Ctrl+C → python3 agent_api.py → Ctrl+B D

# 5. 清理临时文件（可选）
rm /tmp/prompts_andun.py
rm /opt/ReAct_agent/agent_core/prompts.py.zhiyan
