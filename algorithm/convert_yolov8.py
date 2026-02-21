import tensorrt as trt
import os

# 检查 TensorRT 版本
print(f"TensorRT version: {trt.__version__}")

def convert_onnx_to_trt():
    onnx_file = "yolov8n-pose.onnx"
    engine_file = "yolov8n-pose.engine"
    
    if not os.path.exists(onnx_file):
        print(f"Error: {onnx_file} not found!")
        return False
    
    print(f"Converting {onnx_file} to TensorRT engine...")
    
    # 创建 logger
    logger = trt.Logger(trt.Logger.WARNING)
    
    # 创建 builder
    builder = trt.Builder(logger)
    
    # 创建 network
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    
    # 创建 parser
    parser = trt.OnnxParser(network, logger)
    
    # 解析 ONNX 文件
    with open(onnx_file, 'rb') as f:
        if not parser.parse(f.read()):
            print("Failed to parse ONNX file:")
            for i in range(parser.num_errors):
                print(parser.get_error(i))
            return False
    
    print(f"ONNX parsed successfully. Network has {network.num_layers} layers")
    
    # 创建 config
    config = builder.create_builder_config()
    
    # 设置内存池限制（根据 TensorRT 版本）
    try:
        # TensorRT 8.x 及更新版本
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)  # 1GB
        print("Set memory pool limit using set_memory_pool_limit")
    except AttributeError:
        try:
            # 旧版本 TensorRT
            config.max_workspace_size = 1 << 30
            print("Set memory pool limit using max_workspace_size")
        except AttributeError:
            print("Warning: Could not set workspace size")
    
    # 构建引擎
    print("Building TensorRT engine...")
    
    try:
        # 尝试新方法
        serialized_engine = builder.build_serialized_network(network, config)
        print("Used build_serialized_network method")
    except AttributeError:
        try:
            # 回退到旧方法
            engine = builder.build_engine(network, config)
            if engine is None:
                print("Failed to build engine")
                return False
            serialized_engine = engine.serialize()
            print("Used build_engine + serialize method")
        except Exception as e:
            print(f"Error building engine: {e}")
            return False
    
    # 保存引擎文件
    with open(engine_file, 'wb') as f:
        f.write(serialized_engine)
    
    print(f"Engine saved to {engine_file}")
    
    # 验证引擎
    if os.path.exists(engine_file):
        size = os.path.getsize(engine_file) / (1024 * 1024)
        print(f"Engine file size: {size:.2f} MB")
        
        # 尝试加载验证
        try:
            runtime = trt.Runtime(logger)
            with open(engine_file, 'rb') as f:
                engine_data = f.read()
            engine = runtime.deserialize_cuda_engine(engine_data)
            if engine:
                print("Engine verification passed!")
                # 适配TensorRT 10.x版本的API
                if hasattr(engine, 'num_bindings'):
                    # TensorRT 8.x 或 9.x
                    num_bindings = engine.num_bindings
                    print(f"Engine has {num_bindings} bindings")
                    for i in range(num_bindings):
                        name = engine.get_binding_name(i)
                        dtype = engine.get_binding_dtype(i)
                        shape = engine.get_binding_shape(i)
                        io_type = "input" if engine.binding_is_input(i) else "output"
                        print(f"  {io_type}: {name}, dtype: {dtype}, shape: {shape}")
                elif hasattr(engine, 'nb_bindings'):
                    # TensorRT 7.x 或更早版本
                    num_bindings = engine.nb_bindings
                    print(f"Engine has {num_bindings} bindings")
                    for i in range(num_bindings):
                        name = engine.get_binding_name(i)
                        dtype = engine.get_binding_dtype(i)
                        shape = engine.get_binding_shape(i)
                        io_type = "input" if engine.binding_is_input(i) else "output"
                        print(f"  {io_type}: {name}, dtype: {dtype}, shape: {shape}")
                else:
                    # TensorRT 10.x 版本，使用新的API
                    num_io_tensors = engine.num_io_tensors
                    print(f"Engine has {num_io_tensors} bindings")
                    for i in range(num_io_tensors):
                        name = engine.get_tensor_name(i)
                        dtype = engine.get_tensor_dtype(name)
                        shape = engine.get_tensor_shape(name)
                        # 在TensorRT 10.x中，需要通过其他方式判断是否为输入
                        try:
                            # 尝试检查是否为输入（可能需要根据实际情况调整）
                            io_type = "input" if engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT else "output"
                        except:
                            # 如果无法获取tensor mode，使用默认方法或其他方式
                            io_type = "unknown"
                        print(f"  {io_type}: {name}, dtype: {dtype}, shape: {shape}")
                return True
        except Exception as e:
            print(f"Engine verification warning: {e}")
            print("But engine file was created, you can try to use it")
            return True
    
    return False

if __name__ == "__main__":
    success = convert_onnx_to_trt()
    if success:
        print("\n✅ Conversion successful!")
    else:
        print("\n❌ Conversion failed!")