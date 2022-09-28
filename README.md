# 二进制翻译（android arm64 to x86_64）进展

[TOC]

## 2022-09-28

### 问：大部分安卓软件都是 java 开发的吧，那编译后应该是 java binary code，平台无关的，为什么还需要做翻译呢？

- 大部分软件都有 native 的库
- java 现在也是 art 技术 直接编译成机器码了，不再是 java 虚拟机了（安装 apk 应用时完成所有的翻译工作，直接保存机器码。运行时直接动态加载）
- 每个 so 千差万别，没办法统一接口

### 组件介绍

- [安卓模拟器 emulator 介绍](https://developer.android.com/studio/releases/emulator)
- [安卓通用内核 ACK 介绍](https://source.android.com/devices/architecture/kernel/generic-kernel-image)
- [安卓虚拟设备 AVD 介绍](https://source.android.com/docs/setup/create/avd)

### 编译 Android 12

```sh
# 参考 https://gerrit-googlesource.proxy.ustclug.org/git-repo 安装 repo
# 我是手动下载安装的，没有通过 apt 安装。直接安装会依赖 python2.7 ，然后无法解释一些 python 代码
# repo 会直接执行 python 命令，我的 python 版本是 2.7
# 我手动删掉了别的 Python 版本，只保留了 3.8
# repo 找不到 python ，需要链接一下 pythom3.8
mkdir -p ~/.bin
PATH="${HOME}/.bin:${PATH}" # 需要自行修改 ~/.bashrc
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/.bin/repo
chmod a+rx ~/.bin/repo

sudo apt remove python2.7 --auto-remove # https://blog.csdn.net/weixin_43270713/article/details/106427544
sudo apt remove python3.6 --auto-remove
sudo ln -s /usr/bin/python3.8 /usr/bin/python

repo init -u git://mirrors.ustc.edu.cn/aosp/platform/manifest -b android-7.1.0_r3
repo sync -j4 --current-branch --no-tags
# 原本打算使用 android-12.0.0_r3 ，因为需要 200g 的磁盘空间，我电脑不够大，所以改成 android-7.1.0_r3
# 如果网络遇到问题的话上 tuna 看看

# TODO
```

### 计划

- 安卓模拟器跑起来
- 分析里面的二进制翻译怎么做的
- 分别编译 rom 和 host 代码

## 2022-09-27

### 入门

- binary translation 简称 BT
- [二进制翻译( binary translation )有没有成熟的现实应用？请介绍一下实现方式与性能瓶颈。?](https://www.zhihu.com/question/29851229/answer/104193305)
- 下载 IDA ，看了一下 libhoudini 的二进制，完全看不懂

### 参考

- intel 的 BT 项目：libhoudini（未开源，只有二进制）
- qemu 的 User Mode Emulation
- Google Android Studio 某些包含 google 服务的 AVD 镜像里面自带的 libndk_translation.so(好像有符号 没有被 strip 掉)
- 性能是 houdini > AVD > qemu
- qemu 追求通用性 所以会损失很大的性能
- 看到一个 riscv 到 x64 的库，[sfuzz](https://github.com/seal9055/sfuzz)，暂时完全看不懂，不知道能干啥，以后再看
