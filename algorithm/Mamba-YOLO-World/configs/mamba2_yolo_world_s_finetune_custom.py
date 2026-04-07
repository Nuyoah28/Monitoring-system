_base_ = ['../third_party/mmyolo/configs/yolov8/'
          'yolov8_s_syncbn_fast_8xb16-500e_coco.py', 'mamba2_config.py']
custom_imports = dict(imports=['yolo_world'],
                      allow_failed_imports=False)

# ======================================================================
# 类别与元信息定义 (解决 IndexError 的核心)
# ======================================================================
class_names = ('overflow', 'garbage', 'garbage bin', 'bicycle', 'motorcycle', 'fire', 'smoke')
metainfo = dict(classes=class_names)

# ======================================================================
# 微调超参数 (针对 RTX 3090 + 自定义数据集优化)
# ======================================================================
num_classes = 7              # overflow, garbage, garbage_bin, bicycle, motorcycle, fire, smoke
num_training_classes = 7
max_epochs = 100              # 延长至100轮，压榨模型潜能至完全收敛
max_keep_ckpts = 5
close_mosaic_epochs = 10
save_epoch_intervals = 5
text_channels = _base_.TEXT_CHANNELS
text_expand = _base_.TEXT_EXPAND
base_lr = 1e-4               # 微调用更小学习率
weight_decay = 0.05
train_batch_size_per_gpu = 8  # RTX 3090 (24GB) 适配
val_batch_size_per_gpu = 4
val_num_workers = 4
copypaste_prob = 0.3

# ======================================================================
# 加载预训练权重（关键！）
# ======================================================================
load_from = 'algo/mamba2_yolo_world_s.pth'  # 预训练权重路径，按需修改

# ======================================================================
# 模型配置
# ======================================================================
model = dict(
    type='YOLOWorldDetector',
    mm_neck=True,
    num_train_classes=num_training_classes,
    num_test_classes=num_classes,
    data_preprocessor=dict(type='YOLOWDetDataPreprocessor'),
    backbone=dict(
        _delete_=True,
        type='MultiModalYOLOBackbone',
        image_model={{_base_.model.backbone}},
        text_model=dict(
            type='HuggingCLIPLanguageBackbone',
            model_name='openai/clip-vit-base-patch32',
            frozen_modules=['all']      # ★ 冻结 CLIP 文本编码器，保留开放词汇能力
        ),
    ),
    neck=dict(type='MambaYOLOWorldPAFPN',
              guide_expand=text_expand,
              text_emb_dim=text_channels,
              text_extractor=_base_.mamba_cfg,
              block_cfg=dict(type='MambaFusionCSPLayerWithTwoConv2',
                             vss_cfg=_base_.vss_cfg,)
              ),
    bbox_head=dict(type='YOLOWorldHead',
                   head_module=dict(type='YOLOWorldHeadModule',
                                    use_bn_head=True,
                                    embed_dims=text_channels,
                                    num_classes=num_training_classes)),
    train_cfg=dict(assigner=dict(num_classes=num_training_classes))
)

# ======================================================================
# 数据集配置
# ======================================================================
text_transform = [
    dict(type='LoadText',
         text_path='data/texts/custom_finetune_class_texts.json'),
    dict(type='mmdet.PackDetInputs',
         meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'flip',
                    'flip_direction', 'texts'))
]

train_pipeline = [
    *_base_.pre_transform,
    dict(type='MultiModalMosaic',
         img_scale=_base_.img_scale,
         pad_val=114.0,
         pre_transform=_base_.pre_transform),
    dict(type='YOLOv5CopyPaste', prob=copypaste_prob),
    dict(
        type='YOLOv5RandomAffine',
        max_rotate_degree=0.0,
        max_shear_degree=0.0,
        scaling_ratio_range=(1 - _base_.affine_scale, 1 + _base_.affine_scale),
        max_aspect_ratio=_base_.max_aspect_ratio,
        border=(-_base_.img_scale[0] // 2, -_base_.img_scale[1] // 2),
        border_val=(114, 114, 114)),
    *_base_.last_transform[:-1],
    *text_transform
]
train_pipeline_stage2 = [*_base_.train_pipeline_stage2[:-1], *text_transform]

# 训练数据集 —— 指向合并后的 COCO JSON
custom_train_dataset = dict(
    _delete_=True,
    type='MultiModalDataset',
    dataset=dict(
        type='YOLOv5CocoDataset',
        metainfo=metainfo,
        data_root='data/custom_finetune',
        ann_file='annotations/instances_train.json',
        data_prefix=dict(img='images/train/'),
        filter_cfg=dict(filter_empty_gt=False, min_size=32)),
    class_text_path='data/texts/custom_finetune_class_texts.json',
    pipeline=train_pipeline)

train_dataloader = dict(
    batch_size=train_batch_size_per_gpu,
    collate_fn=dict(type='yolow_collate'),
    dataset=custom_train_dataset)

# 测试管线
test_pipeline = [
    *_base_.test_pipeline[:-1],
    dict(type='LoadText',
         text_path='data/texts/custom_finetune_class_texts.json'),
    dict(type='mmdet.PackDetInputs',
         meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape',
                    'scale_factor', 'pad_param', 'texts'))
]

# 验证数据集
custom_val_dataset = dict(
    _delete_=True,
    type='MultiModalDataset',
    dataset=dict(
        type='YOLOv5CocoDataset',
        metainfo=metainfo,
        # data_root='data/custom_finetune/',
        test_mode=True,
        # ann_file='annotations/instances_val.json',
        data_prefix=dict(img='images/val/'),
        batch_shapes_cfg=None,
        return_classes=True,
    ),
    class_text_path='data/texts/custom_finetune_class_texts.json',
    pipeline=test_pipeline,
)

val_dataloader = dict(dataset=custom_val_dataset,
                      pin_memory=False,
                      num_workers=val_num_workers,
                      persistent_workers=True,
                      batch_size=val_batch_size_per_gpu)
test_dataloader = val_dataloader

# 评估器
val_evaluator = dict(type='mmdet.CocoMetric',
                     ann_file='data/custom_finetune/annotations/instances_val.json',
                     metric='bbox',
                     classwise=True)         # 开启详细分类评估，显示Recall/Precision明细
test_evaluator = val_evaluator

# ======================================================================
# 训练策略
# ======================================================================
default_hooks = dict(
    param_scheduler=dict(
        scheduler_type='linear',
        lr_factor=0.01,
        max_epochs=max_epochs),
    checkpoint=dict(
        max_keep_ckpts=max_keep_ckpts,
        rule='greater',
        interval=save_epoch_intervals))

custom_hooks = [
    dict(type='EMAHook',
         ema_type='ExpMomentumEMA',
         momentum=0.0001,
         update_buffers=True,
         strict_load=False,
         priority=49),
    dict(type='mmdet.PipelineSwitchHook',
         switch_epoch=max_epochs - close_mosaic_epochs,
         switch_pipeline=train_pipeline_stage2)
]

train_cfg = dict(max_epochs=max_epochs,
                 val_interval=5,
                 dynamic_intervals=[((max_epochs - close_mosaic_epochs),
                                     _base_.val_interval_stage2)])

# ======================================================================
# 优化器配置（微调策略）
# ======================================================================
optim_wrapper = dict(
    optimizer=dict(
        _delete_=True,
        type='AdamW',
        lr=base_lr,
        weight_decay=weight_decay,
        batch_size_per_gpu=train_batch_size_per_gpu),
    paramwise_cfg=dict(
        custom_keys={
            'backbone': dict(lr_mult=0.01),            # ★ backbone 用极低学习率
            'backbone.text_model': dict(lr_mult=0.0),  # ★ CLIP 完全不更新
            'logit_scale': dict(weight_decay=0.0)
        }),
    constructor='YOLOWv5OptimizerConstructor',
)

# ======================================================================
# 视觉监控配置 (支持 TensorBoard 实时查看指标趋势)
# ======================================================================
visualizer = dict(
    type='mmdet.DetLocalVisualizer',
    vis_backends=[
        dict(type='LocalVisBackend'),       # 保持本地 JSON 记录
        dict(type='TensorboardVisBackend')  # 开启 TensorBoard 记录
    ],
    name='visualizer')

