
#include <iostream>
#include <string>
#include <ctime>
#include <stdio.h>
#include <omp.h>

#include <MNN/MNNDefine.h>
#include <MNN/MNNForwardType.h>
#include <MNN/Interpreter.hpp>

#include "utils.h"
#include "network.h"
#define use_camera 0  //use_camera：是否使用摄像头（当前设为0，不使用）
#define mnnd 1        //mnnd：是否使用mnnd模型（当前设为1，使用mnnd模型）

static const char* OUTPUT_NAME = "output0"; // model output tensor name

std::vector<BoxInfo> decode(cv::Mat &cv_mat, std::shared_ptr<MNN::Interpreter> &net, MNN::Session *session, int INPUT_SIZE)
/*
    这个函数负责对神经网络输出进行解码，提取目标框信息：
*/
{
    // always use NCHW input for this network
    auto inputTensor = net->getSessionInput(session, nullptr);
    auto inShape = inputTensor->shape();
    printf("    **Tensor shape** (after resize):");
    for (auto v : inShape) printf(" %d", v);
    printf("\n");

    // ensure cv_mat is float and has 3 channels
    cv::Mat float_mat;
    if (cv_mat.type() != CV_32FC3) {
        cv_mat.convertTo(float_mat, CV_32FC3);
    } else {
        float_mat = cv_mat;
    }
    if (float_mat.channels() != 3) {
        std::cerr << "unexpected channel count: " << float_mat.channels() << std::endl;
    }

    // prepare NCHW host tensor
    std::vector<int> dims{1, 3, INPUT_SIZE, INPUT_SIZE};
    std::unique_ptr<MNN::Tensor> hostTensor(MNN::Tensor::create<float>(dims, NULL, MNN::Tensor::CAFFE));
    float *dst = hostTensor->host<float>();
    int hw = INPUT_SIZE * INPUT_SIZE;
    const float *src = reinterpret_cast<const float *>(float_mat.data);
    // cv_mat is HWC BGR (converted earlier); we assume preprocess returned RGB
    for (int h = 0; h < INPUT_SIZE; ++h) {
        for (int w = 0; w < INPUT_SIZE; ++w) {
            int idx = h * INPUT_SIZE + w;
            dst[0 * hw + idx] = src[idx * 3 + 0];
            dst[1 * hw + idx] = src[idx * 3 + 1];
            dst[2 * hw + idx] = src[idx * 3 + 2];
        }
    }

    inputTensor->copyFromHostTensor(hostTensor.get());

    net->runSession(session);
    MNN::Tensor *tensor_scores = net->getSessionOutput(session, OUTPUT_NAME);
    if (nullptr == tensor_scores) {
        std::cerr << "Error: can't find output: outputs\n";
        // dump all available outputs for debugging
        const auto &outs = net->getSessionOutputAll(session);
        std::cerr << "  available outputs:";
        for (const auto &p : outs) std::cerr << ' ' << p.first;
        std::cerr << '\n';
        return {}; // return empty detection list
    }
    MNN::Tensor tensor_scores_host(tensor_scores, tensor_scores->getDimensionType());
    tensor_scores->copyToHostTensor(&tensor_scores_host);
    auto pred_dims = tensor_scores_host.shape();

#if mnnd
    const unsigned int num_proposals = pred_dims.at(1);
    const unsigned int num_classes = pred_dims.at(2) - 5;
    std::vector<BoxInfo> bbox_collection;

    for (unsigned int i = 0; i < num_proposals; ++i)
    {
        const float *offset_obj_cls_ptr = tensor_scores_host.host<float>() + (i * (num_classes + 5)); // row ptr
        float obj_conf = offset_obj_cls_ptr[4];
        if (obj_conf < 0.5)
            continue;

        float cls_conf = offset_obj_cls_ptr[5];
        unsigned int label = 0;
        for (unsigned int j = 0; j < num_classes; ++j)
        {
            float tmp_conf = offset_obj_cls_ptr[j + 5];
            if (tmp_conf > cls_conf)
            {
                cls_conf = tmp_conf;
                label = j;
            }
        }

        float conf = obj_conf * cls_conf; 
        if (conf < 0.50)
            continue;

        float cx = offset_obj_cls_ptr[0];
        float cy = offset_obj_cls_ptr[1];
        float w = offset_obj_cls_ptr[2];
        float h = offset_obj_cls_ptr[3];

        float x1 = (cx - w / 2.f);
        float y1 = (cy - h / 2.f);
        float x2 = (cx + w / 2.f);
        float y2 = (cy + h / 2.f);

        BoxInfo box;
        box.x1 = std::max(0.f, x1);
        box.y1 = std::max(0.f, y1);
        box.x2 = std::min(x2, (float)INPUT_SIZE - 1.f);
        box.y2 = std::min(y2, (float)INPUT_SIZE - 1.f);
        box.score = conf;
        box.label = label;
        bbox_collection.push_back(box);
    }
#else
    const unsigned int num_proposals = pred_dims.at(0);
    const unsigned int num_datainfo = pred_dims.at(1);
    std::vector<BoxInfo> bbox_collection;
    for (unsigned int i = 0; i < num_proposals; ++i)
    {
        const float *offset_obj_cls_ptr = tensor_scores_host.host<float>() + (i * num_datainfo); // row ptr
        float obj_conf = offset_obj_cls_ptr[4];
        if (obj_conf < 0.5)
            continue;

        float x1 = offset_obj_cls_ptr[0];
        float y1 = offset_obj_cls_ptr[1];
        float x2 = offset_obj_cls_ptr[2];
        float y2 = offset_obj_cls_ptr[3];

        BoxInfo box;
        box.x1 = std::max(0.f, x1);
        box.y1 = std::max(0.f, y1);
        box.x2 = std::min(x2, (float)INPUT_SIZE - 1.f);
        box.y2 = std::min(y2, (float)INPUT_SIZE - 1.f);
        box.score = offset_obj_cls_ptr[4];
        box.label = offset_obj_cls_ptr[5];
        bbox_collection.push_back(box);
    }
#endif
    // hostTensor will be freed automatically
    return bbox_collection;
}

int main(int argc, char const *argv[])
{
    // 输入尺寸（网络固定）
    const int INPUT_SIZE = 320;

    // 启动天气监测，初始温度25度，湿度50%
    startWeatherMonitoring(25, 50);

    // 加载模型
    std::string model_name = "../models/yolov12_fp16.mnn";

    std::shared_ptr<MNN::Interpreter> net = std::shared_ptr<MNN::Interpreter>(MNN::Interpreter::createFromFile(model_name.c_str()));
    if (nullptr == net)
    {
        stopWeatherMonitoring();
        return 0;
    }

    // 配置推理参数
    MNN::ScheduleConfig config;
    config.numThread = 4;
    config.type = static_cast<MNNForwardType>(MNN_FORWARD_CPU);
    MNN::BackendConfig backendConfig;
    // backendConfig.precision = (MNN::BackendConfig::PrecisionMode)1;
    backendConfig.precision = MNN::BackendConfig::Precision_Low_BF16;
    backendConfig.memory = MNN::BackendConfig::Memory_High;
    backendConfig.power = MNN::BackendConfig::Power_High;
    config.backendConfig = &backendConfig;
    // 创建推理会话
    MNN::Session *session = net->createSession(config);
    // 必须对输入tensor进行resize，并调用resizeSession，否则调用runSession会报 "not resized"
    {
        auto inputTensor = net->getSessionInput(session, nullptr);
        if (nullptr == inputTensor) {
            std::cerr << "getSessionInput returned null" << std::endl;
            stopWeatherMonitoring();
            return -1;
        }
        auto orig = inputTensor->shape();
        printf("input original shape:");
        for (auto v : orig) printf(" %d", v);
        printf("\n");
        std::vector<int> newShape = {1, 3, INPUT_SIZE, INPUT_SIZE};
        net->resizeTensor(inputTensor, newShape);
        net->resizeSession(session);
        // note: resizeSession returns void; if it fails, MNN_ERROR will have been printed earlier by the library
        // verify that the model actually produced outputs after resizing
        bool session_ok = true;
        {
            const auto &outs = net->getSessionOutputAll(session);
            if (outs.empty()) {
                std::cerr << "[ERROR] session has no outputs after resize, model may be incompatible or failed to build.\n";
                session_ok = false;
            }
            std::cerr << "available output tensors:";
            for (const auto &p : outs) std::cerr << ' ' << p.first;
            std::cerr << '\n';
            if (session_ok) {
                // ensure output name exists
                if (outs.find(OUTPUT_NAME) == outs.end()) {
                    std::cerr << "[ERROR] expected output '" << OUTPUT_NAME << "' not found.\n";
                    session_ok = false;
                }
            }
        }
        if (!session_ok) {
            stopWeatherMonitoring();
            return -1;
        }
    }
    // prepare matrix info used for preprocessing
    MatInfo mmat_objection;
    mmat_objection.inpSize = INPUT_SIZE;

    // test run with a blank image to catch any runSession errors early
    {
        cv::Mat dummy(INPUT_SIZE, INPUT_SIZE, CV_32FC3, cv::Scalar(0,0,0));
        cv::Mat pimg = preprocess(dummy, mmat_objection);
        auto testres = decode(pimg, net, session, mmat_objection.inpSize);
        if (testres.empty()) {
            std::cerr << "[ERROR] session test run produced no output, aborting.\n";
            stopWeatherMonitoring();
            return -1;
        }
    }

    std::vector<BoxInfo> bbox_collection;
    cv::Mat image;

// RTMP流初始化和主循环
    cv::VideoCapture capture;
    capture.open("rtmp://192.168.213.197:1935/live/raw");

    cv::Mat frame;
    while (true)
    {
        bbox_collection.clear();
        
        struct timespec begin, end;
        long time;
        clock_gettime(CLOCK_MONOTONIC, &begin);

        // 获取当前帧
        capture >> frame;
        cv::Mat raw_image = frame;

        cv::Mat pimg = preprocess(raw_image, mmat_objection);
        bbox_collection = decode(pimg, net, session, mmat_objection.inpSize);// 模型推理
        if (bbox_collection.empty() && !frame.empty()) {
            // likely session failed; break to avoid endless errors
            std::cerr << "Session failed during inference, aborting loop.\n";
            break;
        }
        nms(bbox_collection, 0.50);// 非极大值抑制去重
        
        // 检查是否检测到需要报警的对象（例如：人、车等）
        for (const auto& box : bbox_collection) {
            // 示例：当检测到person且置信度大于0.7时触发报警
            // 这里可以根据实际需求修改检测条件
            if (box.label == 0 && box.score > 0.7f) {  // 0通常代表person
                triggerAlarm();
                break; // 防止重复触发
            }
        }
        
        //draw_box(raw_image, bbox_collection, mmat_objection);

        // 性能计时
        clock_gettime(CLOCK_MONOTONIC, &end);
        time = (end.tv_sec - begin.tv_sec) + (end.tv_nsec - begin.tv_nsec);
        if(time > 0) printf(">> Time : %lf ms\n", (double)time / 1000000);
    }

    // 程序退出前停止天气监测
    stopWeatherMonitoring();
    return 0;
}
