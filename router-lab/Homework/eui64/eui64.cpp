#include "eui64.h"
#include <stdint.h>
#include <stdlib.h>

in6_addr eui64(const ether_addr mac) {
  in6_addr res = {0};
  // TODO
  // 第 1 个字节为 0xFE，第 2 个字节为 0x80，第 3 到第 8 个字节设为 0
  res.s6_addr[0] = 0xfe;
  res.s6_addr[1] = 0x80;
  for(int i = 2; i < 8; i++){
    res.s6_addr[i] = 0x00;
  }

  // 将 MAC 地址第 1 到第 3 个字节复制到 IPv6 地址的第 9 到第 11 个字节；
  for(int i = 0; i < 3; i++){
    res.s6_addr[i + 8] = mac.ether_addr_octet[i];
  }
  // 再将第 4 到第 6 个字节复制到 IPv6 地址的第 14 到第 16 个字节
  for(int i = 3; i < 6; i++){
    res.s6_addr[i + 10] = mac.ether_addr_octet[i];
  }

  // 设置 IPv6 地址的第 12 个字节为 0xFF，第 13 个字节为 0xFE
  res.s6_addr[11] = 0xff;
  res.s6_addr[12] = 0xfe;

  // 把 IPv6 地址第 9 个字节按网络位序从左到右第 7 位
  // 用 0x02 异或实现
  res.s6_addr[8] = res.s6_addr[8] ^ 0x02;

  return res;
}