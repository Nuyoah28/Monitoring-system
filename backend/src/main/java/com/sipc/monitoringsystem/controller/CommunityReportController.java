package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.CommunityReport.CommunityReportInfo;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.CommunityReportService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.OssUtil;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import jakarta.validation.constraints.NotNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@CrossOrigin
@RequestMapping("/api/v1/community-report")
public class CommunityReportController {

    @Autowired
    private CommunityReportService communityReportService;

    @Autowired
    private UserService userService;

    @Autowired
    private OssUtil ossUtil;

    @GetMapping("/list")
    public CommonResult<List<CommunityReportInfo>> list() {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        return CommonResult.success(communityReportService.listForUser(currentUser));
    }

    @GetMapping("/{id}")
    public CommonResult<CommunityReportInfo> getById(@PathVariable @NotNull Integer id) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        CommunityReportInfo info = communityReportService.getById(id, currentUser);
        if (info == null) {
            return CommonResult.fail("上报记录不存在");
        }
        return CommonResult.success(info);
    }

    @PostMapping("/create")
    public CommonResult<Integer> create(@RequestBody CommunityReportInfo info) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (info == null || info.getCategory() == null || info.getCategory().trim().isEmpty()) {
            return CommonResult.fail("请选择问题分类");
        }
        if (info.getDescription() == null || info.getDescription().trim().isEmpty()) {
            return CommonResult.fail("请填写问题描述");
        }
        Integer id = communityReportService.create(info, currentUser);
        if (id == null || id < 0) {
            return CommonResult.fail("提交上报失败");
        }
        return CommonResult.success(id);
    }

    @PutMapping("/handle")
    public CommonResult<BlankRes> handle(@RequestBody CommunityReportInfo info) {
        if (info == null || info.getId() == null) {
            return CommonResult.fail("id不能为空");
        }
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (currentUser.getRole() == null || currentUser.getRole() != 0) {
            return CommonResult.fail("无权操作");
        }
        if (!communityReportService.handle(info.getId(), info.getStatus(), info.getHandleReply(), currentUser)) {
            return CommonResult.fail("处理上报失败");
        }
        return CommonResult.success("处理成功");
    }

    @DeleteMapping("/{id}")
    public CommonResult<BlankRes> delete(@PathVariable @NotNull Integer id) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (!communityReportService.delete(id, currentUser)) {
            return CommonResult.fail("删除上报失败");
        }
        return CommonResult.success("删除成功");
    }

    @PostMapping("/upload")
    public CommonResult<Map<String, String>> upload(@RequestParam("file") MultipartFile file) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (file == null || file.isEmpty()) {
            return CommonResult.fail("上传文件为空");
        }
        try {
            String objectKey = ossUtil.uploadImage(file);
            Map<String, String> data = new HashMap<>();
            data.put("key", objectKey);
            data.put("url", ossUtil.buildImageUrl(objectKey));
            return CommonResult.success(data);
        } catch (Exception e) {
            log.error("上报图片上传失败", e);
            return CommonResult.fail("图片上传失败");
        }
    }

    private User getCurrentUser() {
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        return tokenUser == null ? null : userService.getById(tokenUser.getId());
    }
}
