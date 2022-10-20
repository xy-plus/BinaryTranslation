# 二进制翻译进展

[TOC]

## 2022-10-19

计划目标：参考 ria-jit（c 语言），使用 rust 编写一个 riscv(or arm) to x86 的翻译器。

发现该项目使用的 riscv gcc 是 2020-09-25 之前的某个版本，如果使用当时的版本，可能会没有 rvc 的问题。但是 2021.01.26 版本之前的 release 是 2020 年的了，感觉太久远了，所以就算找 commit ，也得下载一堆东西自行编译。

- 安装 riscv-gcc

```sh
git clone https://github.com/riscv/riscv-gnu-toolchain --recursive
cd riscv-gnu-toolchain
./configure --with-arch=rv64g --disable-multilib
sudo make linux
```

- 运行 ria-jit

```sh
> mkdir build && cd build && cmake .. && make
> vim hello.c
> riscv64-unknown-linux-gnu-gcc hello.c -static -march=rv64imafd -mabi=lp64d
> ./translator -f a.out
hello world
```

## 2022-10-18

尝试运行 ria-jit 项目。该项目只支持 [RISC-V toolchain gcc](https://github.com/riscv/riscv-gnu-toolchain) 使用 `-static -march=rv64imafd -mabi=lp64d` 编译的程序。

由于这是一个 2021 年初的项目，我直接下载 riscv-gnu-toolchain(tag: 2021.01.16) release 的预编译版本。编译后的程序无法通过 ria-jit 运行。

检查错误原因，发现是 ria-jit 不支持 RVC（RISC-V compressed instructions）。

通过 readelf 检查编译出来的 binary ，确实是 RVC 的。

stack overflow answer：Recompile the riscv-gnu-tool with option --with-arch=rv64g --disable-multilib

git clone 就要好多个 G ，特别久，花了点时间。

## 2022-10-17

找到项目：https://github.com/merryhime/dynarmic

该项目的作用是：用户自行将 arm64 指令拷贝到指定的内存区域中，然后可以通过 dynarmic 在 x64 环境执行。

主要通过 src/dynarmic/interface 与 cpu 交互。

使用 jit 的成员函数设置 cpu 状态。

调用 Jit::Execute 以启动 CPU 执行。

dynarmic 通过调用从内存中读取指令 UserCallbacks::MemoryReadCode 。这些指令然后经过几个阶段：

1. 解码（识别指令的类型并将其分解为字段）
2. 翻译（从指令生成高级 IR）
3. 优化（消除冗余微指令，其他速度改进）
4. 发射（将主机可执行代码生成到内存中）
5. 执行（主机 CPU 跳转到发出代码的开头并运行它）

- 解码：src/frontend/A32/decoder/{arm.h,thumb16.h,thumb32.h}。
- 翻译：src/dynarmic/frontend/A32/translate/translate\_{arm,thumb}.cpp。函数 Translate 获取一个起始内存位置、一些 CPU 状态和内存读取器回调，并返回一个基本的 IR 块。
- IR：src/frontend/ir
- 优化：src/ir_opt
- 发射：src/dynarmic/backend/x64/emit_x64.{h,cpp}
- 执行：src/dynarmic/backend/x64/block_of_code.{h,cpp}，BlockOfCode::RunCode

可以看出这个流程和 qemu 的相关部分差不多，或许可以在这个 base 下工作，因为这个功能更精简。

## 2022-10-13

https://github.com/ria-jit/ria-jit

https://www.researchgate.net/publication/345180829_Dynamic_Binary_Translation_for_RISC-V_code_on_x86-64

搜到一个 riscv 到 x84 的 dynamic binary translation ，c 写的，会比 qemu 简单很多。计划参考该项目，用 rust 写一个 arm to x86 的。

## 2022-10-12

继续分析 qemu 源码。

[qemu tcg 源码分析](./src/tcg.md)

## 2022-10-11

继续分析 qemu 源码。

[qemu 源码分析](./src/qemu.md)

## 2022-10-10

阅读 qemu 源码与二进制翻译相关的部分。

### qemu 部分文件功能

- softmmu/vl.c：最主要的模拟循环，虚拟机环境初始化和 CPU 的执行。
- target/{GUEST_ARCH}/translate.c：将 guest 代码翻译成不同架构的 TCG 操作码。
- tcg/tcg.c：主要的 TCG 代码。
- tcg/{HOST_ARCH}/tcg-target.c：将 TCG 代码转化生成主机代码。
- cpu-exec.c：主要寻找下一个二进制翻译代码块，如果没有找到就请求得到下一个代码块，并且操作生成的代码块。

### 查看 qemu user mode 的二进制翻译效果

```bash
> sudo apt-get install qemu-user gcc-aarch64-linux-gnu -y
> cd src
> aarch64-linux-gnu-as -o aarch64_main.o aarch64_main.S
> aarch64-linux-gnu-ld -o aarch64_main.out aarch64_main.o
> qemu-aarch64 aarch64_main.out
hello world
> qemu-aarch64 -d in_asm,out_asm aarch64_main.out
PROLOGUE: [size=42]
0x55db2825a000:  push   %rbp
0x55db2825a001:  push   %rbx
0x55db2825a002:  push   %r12
0x55db2825a004:  push   %r13
0x55db2825a006:  push   %r14
0x55db2825a008:  push   %r15
0x55db2825a00a:  mov    %rdi,%r14
0x55db2825a00d:  add    $0xfffffffffffffb78,%rsp
0x55db2825a014:  jmpq   *%rsi
0x55db2825a016:  xor    %eax,%eax
0x55db2825a018:  add    $0x488,%rsp
0x55db2825a01f:  pop    %r15
0x55db2825a021:  pop    %r14
0x55db2825a023:  pop    %r13
0x55db2825a025:  pop    %r12
0x55db2825a027:  pop    %rbx
0x55db2825a028:  pop    %rbp
0x55db2825a029:  retq

----------------
IN:
0x0000000000400078:  d2800020      mov x0, #0x1
0x000000000040007c:  100000e1      adr x1, #+0x1c (addr 0x400098)
0x0000000000400080:  58000142      ldr x2, pc+40 (addr 0x4000a8)
0x0000000000400084:  d2800808      mov x8, #0x40
0x0000000000400088:  d4000001      svc #0x0

OUT: [size=98]
0x55db2825a100:  mov    -0x14(%r14),%ebp
0x55db2825a104:  test   %ebp,%ebp
0x55db2825a106:  jl     0x55db2825a156
0x55db2825a10c:  movq   $0x1,0x40(%r14)
0x55db2825a114:  movq   $0x400098,0x48(%r14)
0x55db2825a11c:  mov    $0x4000a8,%ebp
0x55db2825a121:  mov    0x0(%rbp),%rbp
0x55db2825a125:  mov    %rbp,0x50(%r14)
0x55db2825a129:  movq   $0x40,0x80(%r14)
0x55db2825a134:  movq   $0x40008c,0x140(%r14)
0x55db2825a13f:  mov    %r14,%rdi
0x55db2825a142:  mov    $0x2,%esi
0x55db2825a147:  mov    $0x56000000,%edx
0x55db2825a14c:  mov    $0x1,%ecx
0x55db2825a151:  callq  0x55db27ee57b0
0x55db2825a156:  lea    -0x11a(%rip),%rax        # 0x55db2825a043
0x55db2825a15d:  jmpq   0x55db2825a018

hello world
----------------
IN:
0x000000000040008c:  d2800000      mov x0, #0x0
0x0000000000400090:  d2800ba8      mov x8, #0x5d
0x0000000000400094:  d4000001      svc #0x0

OUT: [size=77]
0x55db2825a240:  mov    -0x14(%r14),%ebp
0x55db2825a244:  test   %ebp,%ebp
0x55db2825a246:  jl     0x55db2825a281
0x55db2825a24c:  movq   $0x0,0x40(%r14)
0x55db2825a254:  movq   $0x5d,0x80(%r14)
0x55db2825a25f:  movq   $0x400098,0x140(%r14)
0x55db2825a26a:  mov    %r14,%rdi
0x55db2825a26d:  mov    $0x2,%esi
0x55db2825a272:  mov    $0x56000000,%edx
0x55db2825a277:  mov    $0x1,%ecx
0x55db2825a27c:  callq  0x55db27ee57b0
0x55db2825a281:  lea    -0x105(%rip),%rax        # 0x55db2825a183
0x55db2825a288:  jmpq   0x55db2825a018
```

## 2022-10-05

### qemu-user-mode 介绍

[官网介绍](https://qemu-project.gitlab.io/qemu/user/main.html)

QEMU 既可实现全系统硬件虚拟化，也可在 User Mode 下通过为每个容器提供特定的命名空间实现容器化设计。在 User Mode 下，QEMU 不会模拟所有硬件，而是通过内核代码的 TCG(Tiny Code Generator) 模块对异构应用的二进制代码进行翻译和转换。

### Tiny Code Generator(TCG)

> 参考 https://zhuanlan.zhihu.com/p/392753064

TCG 的作用就是翻译模拟的处理器指令流(被模拟处理器)，然后通过 TCG 后端转换为主机指令流（执行 QEMU 的处理器）。

![](./pic/qemu-translate-process.webp)

TCG 定义了一系列 IR (Intermediate Representation)，将已经翻译的代码块放在转换缓存中，并通过跳转指令将源处理器的指令集和目标处理器的指令集链接在一起。当 Hypervisor 执行代码时，存放于转换缓存中的链接指令可以跳转到指定的代码块，目标二进制代码可不断调用已翻译代码块来运行，直到需要翻译新块为止。在执行的过程中，如果遇到了需要翻译的代码块，执行会暂停并跳回到 Hypervisor，Hypervisor 使用和协调 TCG 对需要进行二进制翻译的源处理器指令集进行转换和翻译并存储到转换缓存中。

### Intel Houdini 比 QEMU 快在哪里？

[知乎上一些人的猜测](https://www.zhihu.com/question/48522805)

### 计划

阅读以下内容：

- [微码生成器](https://gitlab.com/qemu-project/qemu/-/blob/master/tcg/README)
- [动态翻译后端](https://gitlab.com/qemu-project/qemu/-/blob/master/docs/devel/tcg.rst)
- [解码器 1](https://gitlab.com/qemu-project/qemu/-/blob/master/docs/devel/decodetree.rst)
- [解码器 2](https://wiki.qemu.org/Documentation/TCG/backend-ops)
- [解码器 3](https://wiki.qemu.org/Documentation/TCG/frontend-ops)
- [StackOverflow 关于 TCG 动态翻译的讨论](https://stackoverflow.com/questions/20675226/qemu-code-flow-instruction-cache-and-tcg)

## 2022-10-04

续写 2022-09-28 的 `编译 Android 12` 。

原计划：android arm64 to x86_64

修改计划：arm64 to x86_64

因为安卓实在太大了，下载编译都需要巨久。而且因为安卓后端本身也是 linux ，所以就先尝试直接在 x86 机器上运行 arm 程序。

计划先看看 qemu user mode ，周末写出一版初步的分析结果。

## 2022-09-28

### 问：大部分安卓软件都是 java 开发的吧，那编译后应该是 java binary code，平台无关的，为什么还需要做翻译呢？

- 大部分软件都有 native 的库
- java 现在也是 art 技术 直接编译成机器码了，不再是 java 虚拟机了（安装 apk 应用时完成所有的翻译工作，直接保存机器码。运行时直接动态加载）
- 每个 so 千差万别，没办法统一接口

### 安卓组件介绍

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

mkdir ../android-7.1.0_r3
cd ../android-7.1.0_r3
repo init -u git://mirrors.ustc.edu.cn/aosp/platform/manifest -b android-7.1.0_r3
repo sync -j4 --current-branch --no-tags    # 要下载巨久，顺手记录一个查看网速的命令：nload -u M -m eth0
# 原本打算使用 android-12.0.0_r3 ，因为需要 200g 的磁盘空间，我电脑不够大，所以改成 android-7.1.0_r3
# 如果网络遇到问题的话上 tuna 看看
# android-7.1.0_r3 有大约 30g ，把 c 盘撑爆了。。。
# 删除 wsl ，重新安装 wsl 到 d 盘：https://zhuanlan.zhihu.com/p/419242528
```

### 计划

- 安卓模拟器跑起来
- 分析里面的二进制翻译怎么做的
- 分别编译 rom 和 host 代码

## 2022-09-27

### BT 入门

- binary translation 简称 BT
- [二进制翻译( binary translation )有没有成熟的现实应用？请介绍一下实现方式与性能瓶颈。](https://www.zhihu.com/question/29851229/answer/104193305)
- 下载 IDA ，看了一下 libhoudini 的二进制，完全看不懂

### BT 参考项目

- intel 的 BT 项目：libhoudini（未开源，只有二进制）
- qemu 的 User Mode Emulation
- Google Android Studio 某些包含 google 服务的 AVD 镜像里面自带的 libndk_translation.so(好像有符号 没有被 strip 掉)
- 性能是 houdini > AVD > qemu
- qemu 追求通用性 所以会损失很大的性能
- 看到一个 riscv 到 x64 的库，[sfuzz](https://github.com/seal9055/sfuzz)，暂时完全看不懂，不知道能干啥，以后再看
