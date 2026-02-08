#include <MNN/MNNDefine.h>
#include <MNN/MNNForwardType.h>
#include <MNN/Interpreter.hpp>
#include <MNN/ImageProcess.hpp>
#include <opencv2/opencv.hpp>
//#include <cv/cv.hpp>


typedef struct
{
    float x1, y1, x2, y2, score;
    int label;
} BoxInfo;

typedef struct
{
    int inpSize, maxSide, Padw, Padh;
    float ratio;
} MatInfo;

cv::Mat preprocess(cv::Mat &cv_mat, MatInfo &mmat_objection);

void nms(std::vector<BoxInfo> &result, float nms_threshold);
void BgrToRgbNeon(cv::Mat& src, cv::Mat& dst);
void resizeImageNeon(cv::Mat& dstimg, cv::Mat& img, int x, int y);
void copyMakeBorderNeon(cv::Mat& img, cv::Mat& output, int top, int bottom, int left, int right, cv::BorderTypes borderType, cv::Scalar value);
void convertToNeon(cv::Mat& img);
void nmsNeon(std::vector<BoxInfo>& input_boxes, float NMS_THRESH);
void draw_box(cv::Mat &cv_mat, std::vector<BoxInfo> &boxes, MatInfo &mmat_objection);
void checkAndAlert(std::vector<BoxInfo> &boxes);