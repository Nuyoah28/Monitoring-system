<template>
  <div class="agent-page">
    <DashboardLayout @open-profile="goProfile">
      <div class="main-col">
        <article class="card hero-card">
          <div class="section-head hero-head">
            <div>
              <h3>数字助手</h3>
              <p>数字助手常驻在线，支持语音或文字发起交互，可联动平台能力完成告警查询、监控查看与智能问答。</p>
            </div>
            <div class="hero-head-side">
              <div class="service-strip">
                <span v-for="item in serviceHighlights" :key="item" class="service-chip">{{ item }}</span>
              </div>
              <span class="status-pill" :class="currentStageStatus">{{ agentStatusLabel }}</span>
            </div>
          </div>

          <div class="hero-shell">
            <div class="hero-stage">
              <VirtualAgentStage
                :status="currentStageStatus"
                :conversation-active="isRealtimeConversationActive"
                :preview-text="agentPreview"
              />
            </div>

            <ChatPanel
              layout="stage"
              :quick-replies="chatQuickReplies"
              @streaming-change="handleStreamingChange"
              @assistant-preview="handleAssistantPreview"
              @user-submit="handleUserSubmit"
              @voice-state-change="handleVoiceStateChange"
              @realtime-change="handleRealtimeConversationChange"
            />
          </div>
        </article>

        <div class="bottom-grid">
          <article class="card monitor-card">
            <div class="card-title-row">
              <div>
                <h3>监控画面</h3>
                <p class="card-subtitle">点击任意画面后，可继续追问相关告警和联动信息。</p>
              </div>
              <span class="inline-tag">联动提问</span>
            </div>

            <div class="monitor-grid">
              <div v-for="tile in cameraTiles" :key="tile" class="video-tile" @click="openFocus(tile)">
                {{ tile }}
              </div>
            </div>
          </article>

          <article class="card side-card overview-card">
            <div class="card-title-row">
              <div>
                <h3>当前告警概况</h3>
                <p class="card-subtitle">汇总当前累计报警、今日新增和重点类型，便于快速判断整体态势。</p>
              </div>
              <span class="inline-tag">实时总览</span>
            </div>
            <div class="kpi-grid overview-grid">
              <div v-for="card in realtimeOverviewCards" :key="card.label" class="kpi">
                <div class="name">{{ card.label }}</div>
                <div class="num">{{ card.value }}</div>
              </div>
            </div>
          </article>
        </div>
      </div>

      <div class="side-col">
        <article class="card side-card task-card">
          <div class="card-title-row">
            <h3>待办事项</h3>
            <span class="inline-tag">未处理优先</span>
          </div>
          <div class="alarms">
            <div v-for="task in pendingTasks" :key="task" class="alarm">{{ task }}</div>
          </div>
        </article>

        <article class="card side-card summary-card">
          <div class="card-title-row">
            <div>
              <h3>周期总结</h3>
              <p class="card-subtitle">自动整理最近一周或最近一月的报警情况和处理建议。</p>
            </div>
            <button class="mini-action" type="button" :disabled="alarmSummaryLoading" @click="fetchAlarmSummary(false, true)">
              {{ alarmSummaryLoading ? '更新中' : '刷新' }}
            </button>
          </div>

          <div class="summary-toolbar">
            <div class="summary-tabs">
              <button
                v-for="option in summaryOptions"
                :key="option.value"
                class="summary-tab"
                :class="{ active: activeSummaryRange === option.value }"
                type="button"
                @click="activeSummaryRange = option.value"
              >
                {{ option.label }}
              </button>
            </div>
            <span class="summary-updated">{{ summaryUpdatedLabel }}</span>
          </div>

          <div v-if="alarmSummaryError" class="summary-empty">
            <p>{{ alarmSummaryError }}</p>
            <button class="mini-action" type="button" :disabled="alarmSummaryLoading" @click="fetchAlarmSummary(false, true)">
              {{ alarmSummaryLoading ? '更新中' : '重新刷新' }}
            </button>
          </div>
          <template v-else>
            <div class="summary-kpis">
              <div class="summary-kpi"><span>总数</span><strong>{{ selectedAlarmSummary.total }}</strong></div>
              <div class="summary-kpi"><span>已处理</span><strong>{{ selectedAlarmSummary.handled }}</strong></div>
              <div class="summary-kpi"><span>未处理</span><strong>{{ selectedAlarmSummary.pending }}</strong></div>
              <div class="summary-kpi"><span>高等级</span><strong>{{ selectedAlarmSummary.highLevel }}</strong></div>
            </div>

            <p class="summary-overview">{{ selectedAlarmSummary.overview }}</p>

            <div class="summary-section">
              <button class="summary-head" type="button" @click="toggleSummarySection('trend')">
                <span>趋势详情</span>
                <span>{{ summarySectionsOpen.trend ? '收起' : '展开' }}</span>
              </button>
              <div v-show="summarySectionsOpen.trend" class="summary-body">
                <div v-for="item in selectedTrendRows" :key="item.label" class="trend-row">
                  <span>{{ item.label }}</span>
                  <div class="trend-bar"><i :style="{ width: `${getTrendWidth(item.value, selectedTrendMax)}%` }"></i></div>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
            </div>

            <div class="summary-section">
              <button class="summary-head" type="button" @click="toggleSummarySection('focus')">
                <span>重点关注</span>
                <span>{{ summarySectionsOpen.focus ? '收起' : '展开' }}</span>
              </button>
              <div v-show="summarySectionsOpen.focus" class="summary-body">
                <div class="focus-grid">
                  <div class="focus-card"><span>峰值时段</span><strong>{{ selectedAlarmSummary.peakPeriod }}</strong></div>
                  <div class="focus-card"><span>重点区域</span><strong>{{ selectedAlarmSummary.topArea }}</strong></div>
                </div>
                <div class="focus-tags">
                  <span v-for="item in selectedAlarmSummary.topCaseTypes" :key="item.label" class="focus-tag">
                    {{ item.label }} {{ item.value }} 次
                  </span>
                </div>
              </div>
            </div>

            <div class="summary-section">
              <button class="summary-head" type="button" @click="toggleSummarySection('advice')">
                <span>处理建议</span>
                <span>{{ summarySectionsOpen.advice ? '收起' : '展开' }}</span>
              </button>
              <div v-show="summarySectionsOpen.advice" class="summary-body">
                <ul class="advice-list">
                  <li v-for="item in selectedAlarmSummary.suggestions" :key="item">{{ item }}</li>
                </ul>
              </div>
            </div>
          </template>
        </article>
      </div>

    </DashboardLayout>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import DashboardLayout from '@/components/DashboardLayout.vue';
import ChatPanel from '@/components/chat_panel.vue';
import VirtualAgentStage from '@/components/VirtualAgentStage.vue';
import { useUserStore } from '@/stores/user';

type AgentStageStatus = 'idle' | 'listening' | 'thinking' | 'speaking';
type VoiceInteractionState = 'idle' | 'listening' | 'speaking';
type SummaryRange = 'week' | 'month';
type SummarySectionKey = 'trend' | 'focus' | 'advice';

interface AlarmItem {
  id: number;
  name: string;
  eventName: string;
  level: number;
  date: string;
  department: string;
  deal: string;
}

interface TimeBucket {
  period: string;
  cnt: number;
}

interface AlarmSummary {
  total: number;
  handled: number;
  pending: number;
  highLevel: number;
  peakPeriod: string;
  topArea: string;
  overview: string;
  trend: TimeBucket[];
  topCaseTypes: Array<{ label: string; value: number }>;
  suggestions: string[];
}

interface RealtimeAlarmData {
  alarmTotal?: { total?: number; todayNew?: number; dayChange?: number };
  alarmCaseTypeTotalList?: Array<{ caseTypeName?: string; total?: number }>;
}

const router = useRouter();
const userStore = useUserStore();

const cameraTiles = ref<string[]>(['北门实时画面', '地下车库入口实时画面', '中庭实时画面']);
const agentStatus = ref<AgentStageStatus>('idle');
const voiceInteractionState = ref<VoiceInteractionState>('idle');
const agentPreview = ref('您好，我是晓卫，可以通过对话帮您查询告警、监控点、天气情况，并辅助处理常见任务。');
const isChatStreaming = ref(false);
const isRealtimeConversationActive = ref(false);

const alarmList = ref<AlarmItem[]>([]);
const realtimeAlarm = ref<RealtimeAlarmData | null>(null);
const alarmSummaryLoading = ref(false);
const alarmSummaryError = ref('');
const summaryUpdatedAt = ref('');
const activeSummaryRange = ref<SummaryRange>('week');
const summarySectionsOpen = ref<Record<SummarySectionKey, boolean>>({ trend: true, focus: false, advice: true });

const chatQuickReplies = ['未处理告警有多少', '查看最近告警', '查询1号监控点天气', '介绍一下你的服务'];
const serviceHighlights = ['实时语音', '连续对话', '监控联动', '周期总结'];
const summaryOptions = [
  { label: '最近一周', value: 'week' as const },
  { label: '最近一月', value: 'month' as const },
];

let statusTimer: number | null = null;
let summaryRefreshTimer: number | null = null;
const SUMMARY_AUTO_REFRESH_MS = 60 * 1000;

const emptySummary = (label: string): AlarmSummary => ({
  total: 0,
  handled: 0,
  pending: 0,
  highLevel: 0,
  peakPeriod: '暂无数据',
  topArea: '暂无数据',
  overview: `${label}暂无可用报警数据。`,
  trend: [],
  topCaseTypes: [{ label: '暂无高发类型', value: 0 }],
  suggestions: ['当前还没有可用于总结的报警数据，建议保持日常巡检并关注实时预警。'],
});

const alarmSummaries = ref<Record<SummaryRange, AlarmSummary>>({
  week: emptySummary('最近一周'),
  month: emptySummary('最近一月'),
});
const currentStageStatus = computed<AgentStageStatus>(() => {
  if (voiceInteractionState.value === 'speaking') return 'speaking';
  if (voiceInteractionState.value === 'listening') return 'listening';
  return agentStatus.value;
});

const agentStatusLabel = computed(() => {
  if (currentStageStatus.value === 'listening') return '正在倾听';
  if (currentStageStatus.value === 'thinking') return '正在处理';
  if (currentStageStatus.value === 'speaking') return '正在回复';
  return '待命中';
});

const selectedAlarmSummary = computed(() => alarmSummaries.value[activeSummaryRange.value]);
const selectedTrendRows = computed(() => {
  const rows = selectedAlarmSummary.value.trend.filter((item) => item.cnt > 0);
  return (rows.length ? rows : selectedAlarmSummary.value.trend).slice(-6).map((item) => ({ label: item.period, value: item.cnt }));
});
const selectedTrendMax = computed(() => selectedTrendRows.value.reduce((max, item) => Math.max(max, item.value), 1));
const summaryUpdatedLabel = computed(() =>
  alarmSummaryLoading.value ? '正在更新...' : summaryUpdatedAt.value ? `更新于 ${summaryUpdatedAt.value}` : '等待首次汇总',
);

const pendingTasks = computed(() => {
  const pending = alarmList.value.filter((item) => !item.deal?.includes('已处理')).slice(0, 3);
  return pending.length
    ? pending.map((item) => `${item.department || item.name}存在${item.eventName}报警，请尽快复核处理。`)
    : ['当前没有未处理报警，建议继续关注实时对话与巡检联动。', '如需快速复盘近期态势，可切换到最近一周或最近一月总结。'];
});

const realtimeOverviewCards = computed(() => {
  const total = realtimeAlarm.value?.alarmTotal?.total ?? 0;
  const todayNew = realtimeAlarm.value?.alarmTotal?.todayNew ?? 0;
  const dayChange = realtimeAlarm.value?.alarmTotal?.dayChange ?? 0;
  const topType = realtimeAlarm.value?.alarmCaseTypeTotalList?.[0]?.caseTypeName || '暂无';
  return [
    { label: '累计报警', value: `${total}` },
    { label: '今日新增', value: `${todayNew}` },
    { label: '变化趋势', value: dayChange > 0 ? `+${dayChange}` : `${dayChange}` },
    { label: '重点类型', value: topType },
  ];
});

const parseAlarmDate = (value: string): Date | null => {
  const match = value.match(/^(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})$/);
  if (!match) return null;
  const now = new Date();
  const parsed = new Date(now.getFullYear(), Number(match[1]) - 1, Number(match[2]), Number(match[3]), Number(match[4]), 0, 0);
  if (parsed.getTime() > now.getTime() + 24 * 60 * 60 * 1000) parsed.setFullYear(parsed.getFullYear() - 1);
  return parsed;
};

const countBy = (values: string[]) =>
  [...values.reduce((map, value) => (value ? map.set(value, (map.get(value) || 0) + 1) : map), new Map<string, number>()).entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);

const sortTrend = (items: Array<{ period?: string; cnt?: number }>) =>
  [...items]
    .map((item) => ({ period: item.period || '-', cnt: Number(item.cnt || 0) }))
    .sort((a, b) => a.period.localeCompare(b.period));

const buildSuggestions = (label: string, total: number, pending: number, highLevel: number, topArea: string, topType: string) => {
  if (!total) {
    return [`${label}暂无新增报警，建议继续保持日常巡检频率，并关注实时态势变化。`];
  }

  const suggestions: string[] = [];
  if (pending / total >= 0.35) suggestions.push(`未处理报警占比较高，建议优先清理${label}内未处理和高等级事件。`);
  if (highLevel > 0) suggestions.push(`本周期出现 ${highLevel} 条高等级报警，建议安排人工复核并形成闭环记录。`);
  if (topType && topType !== '暂无高发类型') suggestions.push(`高发类型以“${topType}”为主，建议检查对应监控区域和模型阈值设置。`);
  if (topArea && topArea !== '暂无数据') suggestions.push(`重点区域集中在${topArea}，建议增加该区域巡查频率并联动附近摄像头复核。`);
  if (!suggestions.length) suggestions.push('整体处理情况较平稳，建议继续维持当前处置节奏并关注高峰时段。');
  return suggestions;
};

const buildAlarmSummary = (label: string, days: number, history: any): AlarmSummary => {
  const threshold = new Date();
  threshold.setHours(0, 0, 0, 0);
  threshold.setDate(threshold.getDate() - (days - 1));

  const scoped = alarmList.value.filter((item) => {
    const parsed = parseAlarmDate(item.date);
    return parsed ? parsed >= threshold : false;
  });

  const total = scoped.length;
  const handled = scoped.filter((item) => item.deal?.includes('已处理')).length;
  const pending = Math.max(total - handled, 0);
  const highLevel = scoped.filter((item) => Number(item.level) >= 3).length;
  const trend = sortTrend(history?.graph1 || []);
  const topCases = ((history?.graph3 || []) as Array<{ period?: string; cnt?: number }>)
    .map((item) => ({ label: item.period || '未知类型', value: Number(item.cnt || 0) }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value);
  const topCaseTypes = (topCases.length ? topCases : countBy(scoped.map((item) => item.eventName))).slice(0, 3);
  const topArea = countBy(scoped.map((item) => item.department))[0]?.label || '暂无数据';
  const peakPeriod = trend.reduce<{ period: string; cnt: number } | null>((max, item) => (!max || item.cnt > max.cnt ? item : max), null)?.period || '暂无数据';
  const suggestions = buildSuggestions(label, total, pending, highLevel, topArea, topCaseTypes[0]?.label || '暂无高发类型');

  return total
    ? {
        total,
        handled,
        pending,
        highLevel,
        peakPeriod,
        topArea,
        trend,
        topCaseTypes: topCaseTypes.length ? topCaseTypes : [{ label: '暂无高发类型', value: 0 }],
        overview: `${label}共记录 ${total} 条报警，已处理 ${handled} 条，未处理 ${pending} 条，报警高峰集中在 ${peakPeriod}。`,
        suggestions,
      }
    : {
        ...emptySummary(label),
        trend,
        topCaseTypes: topCaseTypes.length ? topCaseTypes : [{ label: '暂无高发类型', value: 0 }],
        suggestions,
      };
};

const clearStatusTimer = (): void => {
  if (statusTimer !== null) {
    window.clearTimeout(statusTimer);
    statusTimer = null;
  }
};

const queueIdle = (delay = 2200): void => {
  clearStatusTimer();
  statusTimer = window.setTimeout(() => {
    agentStatus.value = 'idle';
  }, delay);
};

const getTrendWidth = (value: number, max: number) => (max ? Math.max((value / max) * 100, value > 0 ? 12 : 0) : 0);

const toggleSummarySection = (section: SummarySectionKey) => {
  summarySectionsOpen.value[section] = !summarySectionsOpen.value[section];
};

const fetchMonitors = async (): Promise<void> => {
  userStore.hydrateFromSessionStorage();
  try {
    const { data } = await axios.get('/monitor');
    if (data.code === '00000' && data.data?.length) {
      cameraTiles.value = data.data.slice(0, 3).map((item: { name: string }) => item.name);
    }
  } catch (error) {
    console.error('Failed to fetch monitors', error);
  }
};

const fetchAlarmSummary = async (silent = false, force = false): Promise<void> => {
  userStore.hydrateFromSessionStorage();
  void force;
  if (!silent) alarmSummaryLoading.value = true;
  alarmSummaryError.value = '';
  try {
    const [alarmRes, realtimeRes, weekRes, monthRes] = await Promise.allSettled([
      axios.get('/alarm/query', { params: { pageNum: 1, pageSize: 360 } }),
      axios.get('/alarm/realtime'),
      axios.get('/alarm/query/cnt/history', { params: { defer: 7 } }),
      axios.get('/alarm/query/cnt/history', { params: { defer: 30 } }),
    ]);

    if (alarmRes.status === 'fulfilled') {
      alarmList.value = alarmRes.value.data?.data?.alarmList || [];
    }

    if (realtimeRes.status === 'fulfilled') {
      realtimeAlarm.value = realtimeRes.value.data?.data || null;
    }

    const fallbackWeek = buildAlarmSummary('最近一周', 7, weekRes.status === 'fulfilled' ? weekRes.value.data?.data : undefined);
    const fallbackMonth = buildAlarmSummary('最近一月', 30, monthRes.status === 'fulfilled' ? monthRes.value.data?.data : undefined);
    const hasLocalSummary =
      alarmRes.status === 'fulfilled' ||
      weekRes.status === 'fulfilled' ||
      monthRes.status === 'fulfilled' ||
      realtimeRes.status === 'fulfilled';

    if (!hasLocalSummary) {
      alarmSummaryError.value = '暂时无法获取报警总结，请稍后刷新重试。';
      return;
    }

    alarmSummaries.value = {
      week: fallbackWeek,
      month: fallbackMonth,
    };

    summaryUpdatedAt.value = new Date().toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    console.error('Failed to fetch alarm summary', error);
    alarmSummaryError.value = '暂时无法获取报警总结，请稍后刷新重试。';
  } finally {
    alarmSummaryLoading.value = false;
  }
};

const scheduleNextSummaryRefresh = (): void => {
  if (summaryRefreshTimer !== null) {
    window.clearInterval(summaryRefreshTimer);
    summaryRefreshTimer = null;
  }

  summaryRefreshTimer = window.setInterval(() => {
    void fetchAlarmSummary(true);
  }, SUMMARY_AUTO_REFRESH_MS);
};
const handleStreamingChange = (value: boolean): void => {
  isChatStreaming.value = value;
  clearStatusTimer();
  if (value) {
    agentStatus.value = 'thinking';
    agentPreview.value = '已接收您的请求，正在调用平台能力整理结果。';
    return;
  }
  agentStatus.value = 'speaking';
  if (voiceInteractionState.value !== 'speaking') queueIdle();
};

const handleAssistantPreview = (text: string): void => {
  if (!text.trim()) return;
  agentPreview.value = '最新回复已生成，请在左下角消息区查看完整内容。';
  if (!isChatStreaming.value && voiceInteractionState.value !== 'speaking') {
    agentStatus.value = 'speaking';
    queueIdle();
  }
};

const handleUserSubmit = (text: string): void => {
  void text;
  agentStatus.value = 'listening';
  agentPreview.value = '已收到您的问题，正在准备联动查询与回答。';
};

const handleVoiceStateChange = (state: VoiceInteractionState): void => {
  voiceInteractionState.value = state;
  if (state === 'listening') {
    clearStatusTimer();
    agentPreview.value = '正在倾听您的语音输入，请继续说话。';
    return;
  }
  if (state === 'speaking') {
    clearStatusTimer();
    return;
  }
  if (!isChatStreaming.value && agentStatus.value === 'speaking') queueIdle();
};

const handleRealtimeConversationChange = (value: boolean): void => {
  isRealtimeConversationActive.value = value;
  if (value) {
    clearStatusTimer();
    agentStatus.value = 'listening';
    return;
  }
  if (!isChatStreaming.value && voiceInteractionState.value === 'idle') {
    agentStatus.value = 'idle';
    queueIdle(1600);
  }
};

const goProfile = (): void => {
  router.push('/home');
};

const openFocus = (camera: string): void => {
  agentPreview.value = `已选中 ${camera}，可继续追问该画面的告警与联动信息。`;
  agentStatus.value = 'listening';
  queueIdle(1800);
};

onMounted(() => {
  userStore.hydrateFromSessionStorage();
  void Promise.all([fetchMonitors(), fetchAlarmSummary(false)]);
  scheduleNextSummaryRefresh();
});

onBeforeUnmount(() => {
  clearStatusTimer();
  if (summaryRefreshTimer !== null) window.clearInterval(summaryRefreshTimer);
});
</script>

<style scoped>
.agent-page {
  min-height: 100vh;
}

.agent-page :deep(.dash) {
  min-height: 100vh;
  min-height: 100dvh;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  padding-bottom: 0;
}

.agent-page :deep(.grid) {
  grid-template-columns: minmax(0, 1.72fr) minmax(19rem, 0.82fr);
  align-items: stretch;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.main-col,
.side-col {
  display: grid;
  gap: 0.85rem;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.main-col {
  grid-template-rows: minmax(0, 1.56fr) minmax(16rem, 0.8fr);
}

.side-col {
  grid-template-rows: minmax(8rem, 0.34fr) minmax(18rem, 1fr);
}

.hero-card,
.monitor-card,
.summary-card,
.side-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.hero-card {
  gap: 0.95rem;
  padding: 1rem;
  background:
    radial-gradient(circle at 12% 0%, rgba(126, 197, 255, 0.12), transparent 26%),
    linear-gradient(180deg, rgba(18, 48, 79, 0.86), rgba(11, 28, 48, 0.8));
  box-shadow:
    inset 0 0 0 1px rgba(126, 197, 255, 0.08),
    0 20px 44px rgba(4, 12, 24, 0.16);
}

.monitor-card,
.summary-card,
.side-card {
  background:
    linear-gradient(180deg, rgba(17, 46, 75, 0.82), rgba(13, 33, 56, 0.8));
  box-shadow: inset 0 0 0 1px rgba(126, 197, 255, 0.07);
}

.summary-card {
  overflow: auto;
}

.section-head,
.card-title-row,
.summary-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.hero-head {
  align-items: center;
}

.hero-head-side {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
}

.section-head h3,
.card-title-row h3 {
  margin: 0 0 0.24rem;
}

.section-head p,
.card-subtitle {
  margin: 0;
  color: var(--sub);
  line-height: 1.58;
  font-size: 0.88rem;
  max-width: 42rem;
}

.service-strip,
.summary-tabs,
.focus-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.service-chip,
.status-pill,
.inline-tag,
.summary-updated,
.summary-tab,
.mini-action,
.summary-head,
.focus-tag {
  border: 1px solid rgba(126, 197, 255, 0.22);
  background: rgba(17, 47, 75, 0.78);
  color: #eaf6ff;
}

.service-chip,
.status-pill,
.inline-tag,
.summary-updated,
.summary-tab,
.mini-action,
.focus-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.42rem 0.8rem;
  border-radius: 999px;
  font-size: 0.78rem;
}

.status-pill.listening {
  border-color: rgba(248, 203, 113, 0.42);
  color: #f8cb71;
}

.status-pill.thinking,
.status-pill.speaking {
  border-color: rgba(83, 213, 165, 0.42);
  color: #8de7c0;
}

.hero-shell {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border-radius: 30px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background:
    radial-gradient(circle at 80% 14%, rgba(126, 197, 255, 0.08), transparent 24%),
    radial-gradient(circle at 0% 100%, rgba(83, 213, 165, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(8, 25, 43, 0.96), rgba(7, 18, 32, 0.98));
  box-shadow: 0 22px 48px rgba(3, 10, 20, 0.28);
}

.hero-shell::before,
.hero-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-shell::before {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 24%),
    radial-gradient(circle at 20% 18%, rgba(126, 197, 255, 0.12), transparent 22%);
}

.hero-shell::after {
  inset: auto -8% -42% 44%;
  height: 72%;
  background: radial-gradient(circle, rgba(126, 197, 255, 0.12), rgba(126, 197, 255, 0));
  filter: blur(34px);
}

.hero-stage {
  height: 100%;
  min-height: 0;
  padding: 0.9rem;
}

.hero-shell :deep(.virtual-agent) {
  height: 100%;
}

.hero-shell :deep(.stage-shell) {
  min-height: 100%;
  height: 100%;
}

.bottom-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.34fr) minmax(18rem, 0.72fr);
  gap: 0.85rem;
  min-height: 0;
  height: 100%;
}

.summary-toolbar {
  margin: 0.15rem 0 0.7rem;
  align-items: center;
}

.summary-tab,
.mini-action,
.summary-head {
  cursor: pointer;
  transition: all 0.2s ease;
}

.summary-tab.active,
.summary-tab:hover,
.mini-action:hover,
.summary-head:hover {
  border-color: rgba(126, 197, 255, 0.42);
  background: rgba(34, 79, 118, 0.92);
}

.summary-kpis,
.focus-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.summary-kpi,
.focus-card {
  padding: 0.78rem 0.84rem;
  border-radius: 14px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background: rgba(14, 42, 67, 0.56);
}

.summary-kpi span,
.focus-card span {
  display: block;
  margin-bottom: 0.24rem;
  color: rgba(196, 221, 242, 0.7);
  font-size: 0.75rem;
}

.summary-overview {
  margin: 0.78rem 0;
  padding: 0.82rem 0.9rem;
  border-radius: 14px;
  background: rgba(14, 42, 67, 0.44);
  border: 1px solid rgba(126, 197, 255, 0.12);
  color: #ebf6ff;
  line-height: 1.62;
  font-size: 0.86rem;
}

.summary-section + .summary-section {
  margin-top: 0.62rem;
}

.summary-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.66rem 0.8rem;
  border-radius: 12px;
  font-size: 0.82rem;
}

.summary-body {
  margin-top: 0.45rem;
}

.trend-row {
  display: grid;
  grid-template-columns: 4.4rem minmax(0, 1fr) 2rem;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.45rem;
}

.trend-bar {
  height: 0.46rem;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.trend-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(126, 197, 255, 0.86), rgba(83, 213, 165, 0.86));
}

.advice-list {
  margin: 0;
  padding-left: 1.1rem;
  color: #ebf6ff;
  line-height: 1.62;
  font-size: 0.84rem;
}

.summary-empty {
  display: grid;
  gap: 0.85rem;
  place-items: center;
  min-height: 10rem;
  padding: 1rem;
  text-align: center;
  color: rgba(214, 236, 255, 0.8);
  border-radius: 12px;
  border: 1px dashed rgba(126, 197, 255, 0.22);
}

.summary-empty p {
  margin: 0;
  max-width: 18rem;
  line-height: 1.6;
}

.monitor-card .monitor-grid {
  flex: 1;
  min-height: 0;
}

.monitor-card :deep(.video-tile) {
  min-height: 0;
  height: 100%;
}

.side-card .alarms {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.task-card {
  padding-bottom: 0.75rem;
}

.task-card .alarm {
  min-height: 0;
  padding: 0.7rem 0.75rem;
  line-height: 1.48;
}

.overview-card {
  justify-content: space-between;
}

.overview-grid {
  gap: 0.55rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 1500px) {
  .agent-page :deep(.grid) {
    grid-template-columns: minmax(0, 1.54fr) minmax(17.5rem, 0.9fr);
  }
}

@media (max-width: 1320px) {
  .agent-page :deep(.dash) {
    height: auto;
    overflow: auto;
    padding-bottom: 1rem;
  }

  .agent-page :deep(.grid),
  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .main-col,
  .side-col {
    height: auto;
    overflow: visible;
    grid-template-rows: auto auto;
  }

  .main-col {
    order: 1;
  }

  .side-col {
    order: 2;
  }

  .hero-shell {
    overflow: visible;
  }

  .hero-stage {
    padding: 0.82rem;
  }

  .summary-card {
    min-height: 24rem;
  }
}

@media (max-width: 900px) {
  .summary-kpis,
  .focus-grid {
    grid-template-columns: 1fr;
  }

  .trend-row {
    grid-template-columns: 3.4rem minmax(0, 1fr) 1.8rem;
  }
}

@media (max-width: 760px) {
  .section-head,
  .card-title-row,
  .summary-toolbar,
  .hero-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-card,
  .monitor-card,
  .summary-card,
  .side-card {
    padding: 0.88rem;
  }

  .hero-stage {
    padding: 0;
  }
}
</style>


