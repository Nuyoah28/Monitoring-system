package com.sipc.monitoringsystem.model.dto.res.Monitor;

import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

/**
 * @author CZCZCZ
 *         &#064;date 2023-10-01 21:02
 */

@Data
public class GetMonitorListRes {
    // TODO 改字段的时候要改这里

    @Data
    public static class MonitorBorder {

        public MonitorBorder(Monitor monitor) {
            this.leftX = monitor.getLeftX();
            this.leftY = monitor.getLeftY();
            this.rightX = monitor.getRightX();
            this.rightY = monitor.getRightY();
        }

        private Integer leftX;
        private Integer leftY;
        private Integer rightX;
        private Integer rightY;
    }

    @Data
    public static class MonitorAbility {
        public MonitorAbility(Integer caseType, Boolean checked) {
            this.name = caseType == 1 ? "进入危险区域"
                    : caseType == 2 ? "烟雾"
                            : caseType == 3 ? "区域停留"
                                    : caseType == 4 ? "摔倒"
                                            : caseType == 5 ? "明火"
                                                    : caseType == 6 ? "吸烟"
                                                            : caseType == 7 ? "打架"
                                                                    : caseType == 8 ? "垃圾乱放"
                                                                            : caseType == 9 ? "冰面"
                                                                                    : caseType == 10 ? "电动车进楼"
                                                                                            : caseType == 11 ? "载具占用车道"
                                                                                                    : caseType == 12
                                                                                                            ? "挥手呼救"
                                                                                                            : "未知功能";
            this.value = caseType;
            this.checked = checked;
        }

        private String name;
        private Integer value;
        private Boolean checked;
    }

    public GetMonitorListRes(Monitor monitor) {
        this.id = monitor.getId();
        this.number = monitor.getId().toString(); // 新增：摄像头编号（使用ID）
        this.name = monitor.getName();
        this.deal = monitor.getRunning() ? "正在运行" : "停止";
        this.department = monitor.getArea();
        this.leader = monitor.getLeader();
        this.running = monitor.getRunning();
        this.video = "http://8.152.219.117:1975/flv?port=1985&app=live&stream=test" + monitor.getId();
        this.border = new ArrayList<>();
        if (!(monitor.getLeftX() == null || monitor.getLeftY() == null || monitor.getRightX() == null
                || monitor.getRightY() == null)) {
            this.border.add(new MonitorBorder(monitor));
        }
        this.ability = new ArrayList<>();
        // this.ability.add(new MonitorAbility(1,monitor.getDangerArea()));
        this.ability.add(new MonitorAbility(3, monitor.getFall()));
        this.ability.add(new MonitorAbility(4, monitor.getFlame()));
        this.ability.add(new MonitorAbility(5, monitor.getSmoke()));
        this.ability.add(new MonitorAbility(6, monitor.getPunch()));
    }

    private Integer id;
    private String number; // 新增：摄像头编号
    private String name;
    private String deal;
    private String department;
    private String leader;
    private Boolean running;
    private List<MonitorBorder> border;
    private String video;
    private List<MonitorAbility> ability;

}
