# 部署 Headscale 和 DERP 服务实现异地组网

## WireGuard 和 [Tailscale](https://tailscale.com/)

WireGuard 相比于传统 VPN 的核心优势是没有 VPN 网关，所有节点之间都可以点对点
（P2P）连接，也就是我之前提到的 全互联模式（full mesh），效率更高，速度更快，成
本更低。

WireGuard 目前最大的痛点就是上层应用的功能不够健全，因为 WireGuard 推崇的是 Unix
的哲学，WireGuard 本身只是一个内核级别的模块，只是一个数据平面，至于上层的更高级
的功能（比如秘钥交换机制，UDP 打洞，ACL 等），需要通过用户空间的应用来实现。

Tailscale 是一种基于 WireGuard 的虚拟组网工具，Tailscale 是在用户态实现了
WireGuard 协议

1. 开箱即用
  - 无需配置防火墙
  - 没有额外的配置

2. 高安全性/私密性
  - 自动密钥轮换
  - 点对点连接
  - 支持用户审查端到端的访问记录

3.  在原有的 ICE、STUN 等 UDP 协议外，实现了 DERP TCP 协议来实现 NAT 穿透

4. 基于公网的控制服务器下发 ACL 和配置，实现节点动态更新

5. 通过第三方（如 Google） SSO 服务生成用户和私钥，实现身份认证

![tailscale-admin](../static/tailscale/tailscale-admin.jpg)

## NAT 穿透
大部分机器都使用私有 IP 地址，如果它们需要访问公网服务，那么需要：

出向流量：需要经过一台 NAT 设备，它会对流量进行 SNAT，将私有 srcIP+Port 转 换成
NAT 设备的公网 IP+Port（这样应答包才能回来），然后再将包发出去；应答流量（入
向）：到达 NAT 设备后进行相反的转换，然后再转发给客户端。

### STUN 是什么
Tailscale 的终极目标是让两台处于网络上的任何位置的机器建立点对点连接（直连），但
现实世界是复杂的，大部份情况下机器都位于 NAT 和防火墙后面，这时候就需要通过打洞
来实现直连，也就是 NAT 穿透。

NAT 按照 NAT 映射行为和有状态防火墙行为可以分为多种类型，但对于 NAT 穿透来说根本
不需要关心这么多类型，只需要看 NAT 或者有状态防火墙是否会严格检查目标 Endpoint，
根据这个因素，可以将 NAT 分为 Easy NAT 和 Hard NAT。

Easy NAT 及其变种称为 “Endpoint-Independent Mapping” (EIM，终点无关的映射)这里的
Endpoint 指的是目标 Endpoint，也就是说，有状态防火墙只要看到有客户端自己发起的出
向包，就会允许相应的入向包进入，不管这个入向包是谁发进来的都可以。

Hard NAT 以及变种称为 “Endpoint-Dependent Mapping”（EDM，终点相关的映射）这种
NAT 会针对每个目标 Endpoint 来生成一条相应的映射关系。 在这样的设备上，如果客户
端向某个目标 Endpoint 发起了出向包，假设客户端的公网 IP 是 2.2.2.2，那么有状态防
火墙就会打开一个端口，假设是 4242。那么只有来自该目标 Endpoint 的入向包才允许通
过 2.2.2.2:4242，其他客户端一律不允许。这种 NAT 更加严格，所以叫 Hard NAT。

对于 Easy NAT，我们只需要提供一个第三方的服务，它能够告诉客户端“它看到的客户端的
公网 ip:port 是什么”，然后将这个信息以某种方式告诉通信对端（peer），后者就知道该
和哪个地址建连了！这种服务就叫 STUN (Session Traversal Utilities for NAT，NAT会
话穿越应用程序)。它的工作流程如下图所示：

![nat-stun-2](../static/tailscale/nat-stun-2.png)

- 笔记本向 STUN 服务器发送一个请求：“从你的角度看，我的地址什么？”
- STUN 服务器返回一个响应：“我看到你的 UDP 包是从这个地址来的：ip:port”。

### 中继是什么

对于 Hard NAT 来说，STUN 就不好使了，即使 STUN 拿到了客户端的公网 ip:port 告诉通
信对端也于事无补，因为防火墙是和 STUN 通信才打开的缺口，这个缺口只允许 STUN 的入
向包进入，其他通信对端知道了这个缺口也进不来。通常企业级 NAT 都属于 Hard NAT。

这种情况下打洞是不可能了，但也不能就此放弃，可以选择一种折衷的方式：创建一个中继
服务器（relay server），客户端与中继服务器进行通信，中继服务器再将包中继
（relay）给通信对端。

至于中继的性能，那要看具体情况了：

如果能直连，那显然没必要用中继方式；但如果无法直连，而中继路径又非常接近双方直连
的真实路径，并且带宽足够大，那中继方式并不会明显降低通信质量。延迟肯定会增加一
点，带宽会占用一些，但相比完全连接不上，还是可以接受的。事实上对于大部分网络而
言，Tailscale 都可以通过各种黑科技打洞成功，只有极少数情况下才会选择中继，中继只
是一种 fallback 机制。

### 中继协议：TURN、DERP

1. TURN (Traversal Using Relays around NAT)：经典方式，核心理念是
  - 用户（人）先去公网上的 TURN 服务器认证，成功后后者会告诉你：“我已经为你分配了
ip:port，接下来将为你中继流量”
  - 然后将这个 ip:port 地址告诉对方，让它去连接这个
地址，接下去就是非常简单的客户端/服务器通信模型了。 

Tailscale 并不使用 TURN。这种协议用起来并不是很好，而且与 STUN 不同， 它没有真正
的交互性，因为互联网上并没有公开的 TURN 服务器。

2. DERP服务器
  - DERP (Detoured Encrypted Routing Protocol) 是一个通用目的包中继协议，运行在
    HTTP 之上，而大部分网络都是允许 HTTP 通信的。
  - 它根据目的公钥（destination’s public key）来中继加密的流量（encrypted payloads）。

Tailscale 使用的算法很有趣，所有客户端之间的连接都是先选择 DERP 模式（中继模
式），这意味着连接立即就能建立（优先级最低但 100% 能成功的模式），用户不用任何等
待。然后开始并行地进行路径发现，通常几秒钟之后，我们就能发现一条更优路径，然后将
现有连接透明升级（upgrade）过去，变成点对点连接（直连）。

因此，DERP 既是 Tailscale 在 NAT 穿透失败时的保底通信方式（此时的角色与 TURN 类
似），也是在其他一些场景下帮助我们完成 NAT 穿透的旁路信道。 换句话说，它既是我们
的保底方式，也是有更好的穿透链路时，帮助我们进行连接升级（upgrade to a
peer-to-peer connection）的基础设施。

![tailscale-relay](https://tailscale.com/assets/84113/1676992987-tailscale-relay.svg)


## 内网穿透常用工具

### [FRP](https://github.com/fatedier/frp)
 ![frp-architecture](../static/tailscale/frp-architecture.png) 
  - 简单高效，需要注意安全问题

### [ZeroTier](https://www.zerotier.com/)
Zerotier 组网中节点分为三个部分，分别是位于国外的中央服务器 Planet，用户自建节点 Moon，以及用户其他节点 Leaf。
![zerotier](../static/tailscale/zerotier.jpg)


## Headscale 是什么

Headscale 由欧洲航天局的 Juan Font 使用 Go 语言开发，在 BSD 许可下发布，实现了
Tailscale 控制服务器的所有主要功能，可以部署在企业内部，没有任何设备数量的限制，
且所有的网络流量都由自己控制。

###  部署 Headscale

创建相关配置，数据库文件
``` bash
mkdir -p ./headscale/config
cd ./headscale
touch ./config/db.sqlite
# 默认配置
wget https://github.com/juanfont/headscale/raw/main/config-example.yaml -O ./headscale/config.yaml
```

自定义控制服务器配置
``` yaml
# config.yaml
# 填写自己的服务器公网 IP 地址和端口，这里自定义端口为 8090，可以换成别的
server_url: http://X.X.X.X:8090
listen_addr: 0.0.0.0:8090
metrics_listen_addr: 0.0.0.0:9090
grpc_listen_addr: 127.0.0.1:50443
grpc_allow_insecure: false
private_key_path: ./private.key
noise:
  private_key_path: ./noise_private.key

# IPV4 在前，这 tailscale status 默认才能输出 IPV4 地址
ip_prefixes:
  - 100.64.0.0/10
  - fd7a:115c:a1e0::/48

derp:
  server:
    enabled: false
    region_id: 901
    region_code: 'beijing-1'
    region_name: 'TecentCloud Beijing-1'
    stun_listen_addr: '0.0.0.0:3478'
  urls:
    - http://X.X.X.X:9999/derp.json
    # - https://controlplane.tailscale.com/derpmap/default
  paths: []
  auto_update_enabled: true
  update_frequency: 24h

disable_check_updates: false
ephemeral_node_inactivity_timeout: 30m
node_update_check_interval: 10s
db_type: sqlite3
db_path: ./db.sqlite
acme_url: https://acme-v02.api.letsencrypt.org/directory
acme_email: ''
tls_letsencrypt_hostname: ''
tls_letsencrypt_cache_dir: ./cache
tls_letsencrypt_challenge_type: HTTP-01
tls_letsencrypt_listen: ':http'
tls_cert_path: ''
tls_key_path: ''

log:
  format: text
  level: info

# 权限控制文件相对路径
# acl_policy_path: './acls.hujson'
acl_policy_path: ''

dns_config:
  override_local_dns: true
  nameservers:
    - 8.8.8.8
    - 114.114.114.114
    - 223.5.5.5
  domains: []
  magic_dns: true
  # 可以自定义为自己的域名
  base_domain: example.com

unix_socket: ./headscale.sock
unix_socket_permission: '0770'
logtail:
  enabled: false
randomize_client_port: false
```

创建用户并在控制服务器上注册
``` bash
docker exec headscale \
  headscale users create shiyang

docker exec headscale \
  headscale nodes register \
  --user shiyang  \
  --key nodekey:XXXXXXXX
```

# 部署 DERP 服务器（无备案域名）
- 准备 derp.json 配置文件
``` json
{
  "Regions": {
    "901": {
      "RegionID": 901,
      "RegionCode": "bejing-1",
      "RegionName": "TecentCloud Beijing-1",
      "Nodes": [
        {
          "Name": "901a",
          "RegionID": 901,
          "DERPPort": 443,
          "HostName": "X.X.X.X",
          "IPv4": "X.X.X.X",
          "InsecureForTests": true
        }
      ]
    }
   }
}
```

- 启动 derper 服务器
``` bash
docker run -d \
--restart always \
--name derper -p 443:443 -p 3478:3478/udp \
-v /var/run/tailscale/tailscaled.sock:/var/run/tailscale/tailscaled.sock \
-e DERP_ADDR=:443 \
ghcr.io/yangchuansheng/ip_derper
```

### Tailscale 客户端接入

### macOS 
``` bash
Applications/Tailscale.app/Contents/MacOS/Tailscale up --login-server http://X.X.X.X:8090 --force-reauth
```
### Linux

安装 tailscale
``` bash
opkg update
opkg install libustream-openssl ca-bundle kmod-tun
tailscale start
```

#### 在 OpenWRT 启动子网路由功能，并开启出口节点模式（手机自动出国）

可以设置一个“子网路由器”（以前称为中继节点）来从 Tailscale 访问这些设备。子网路
由器充当网关，将流量从 Tailscale 网络中继到物理子网。子网路由器尊重访问控制策略
等功能，无需在每台设备上安装该应用程序。

![talscale-subnets](../static/tailscale/tailscale-subnets.png)

![exit-node-02](../static/tailscale/exit-node-02.svg)

设置 IPv4 与 IPv6 路由转发：

``` bash
echo 'net.ipv4.ip_forward = 1' | tee /etc/sysctl.d/ipforwarding.conf
echo 'net.ipv6.conf.all.forwarding = 1' | tee -a /etc/sysctl.d/ipforwarding.conf
sysctl -p /etc/sysctl.d/ipforwarding.conf
```

在 OpenWRT 启动 tailscale

``` bash
tailscale up \
--accept-dns=false \
--netfilter-mode=off \
--accept-routes  \
--advertise-routes=192.168.1.0/24 \
--advertise-exit-node \
–exit-node \ 
--login-server=http://x.x.x.x:8090 --reset
```

查看 headscale 所有已经注册的节点
``` bash
docker exec headscale headscale nodes list
```
![device](../static/tailscale/registered-device.jpg)

查看 headscale 所有路由，开启子网路由功能
``` bash
docker exec headscale headscale routes list
ID | Machine | Prefix         | Advertised | Enabled | Primary
1  | openwrt | 192.168.1.0/24 | true       | true    | true
2  | openwrt | 0.0.0.0/0      | true       | true    | -
3  | openwrt | ::/0           | true       | true    | -

docker exec headscale headscale routes enable -r 1
```


### 安卓设备使用 OpenWRT 作为出口节点
![tailscale-android](../static/tailscale/tailscale-android.jpg)

### 连接与延迟
![netcheck](../static/tailscale/netcheck.jpg)


### TODO: ACL 权限控制配置

## 参考资料

- [Container - Headscale](https://headscale.net/running-headscale-container/)
- [[译] NAT 穿透是如何工作的：技术原理及企业级实践（Tailscale, 2020）](https://arthurchiao.art/blog/how-nat-traversal-works-zh/)
- [How Tailscale works · Tailscale](https://tailscale.com/blog/how-tailscale-works/)
- [Subnet routers and traffic relay nodes · Tailscale](https://tailscale.com/kb/1019/subnets/)
- [Tailscale 基础教程：Headscale 的部署方法和使用教程](https://icloudnative.io/posts/how-to-set-up-or-migrate-headscale)
- [Tailscale 基础教程：部署私有 DERP 中继服务器](https://icloudnative.io/posts/custom-derp-servers)
- [Headscale 部署和 DERP 服务器配置 - Phyng 的博客](https://phyng.com/2023/04/06/headscale.html)
- [Tailscale玩法之内网穿透、异地组网、全隧道模式、纯IP的双栈DERP搭建、Headscale协调服务器搭建](https://www.youtube.com/watch?v=mgDpJX3oNvI)
