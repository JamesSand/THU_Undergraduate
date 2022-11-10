#include "checksum.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include<vector>
#include<iostream>
using namespace std;

bool validateAndFillChecksum(uint8_t *packet, size_t len) {
  // TODO
  struct ip6_hdr *ip6 = (struct ip6_hdr *)packet;

  // check next header
  uint8_t nxt_header = ip6->ip6_nxt;
  if (nxt_header == IPPROTO_UDP) {
    // UDP
    struct udphdr *udp = (struct udphdr *)&packet[sizeof(struct ip6_hdr)];
    
    uint16_t checksum_store = udp->uh_sum;
    udp->uh_sum = 0;

    vector<uint16_t> to_do_list;
    // 加入源地址和目的地址
    for(int i = 8; i < 40; i += 2){
      uint16_t combine = (packet[i] << 8) + packet[i + 1];
      to_do_list.push_back(combine);
    }
    // 加入 udp length
    to_do_list.push_back(htons(udp->uh_ulen));

    // 加入 next protocol
    uint16_t next_protocol = 17;
    to_do_list.push_back(next_protocol);

    // 加入 udp 剩余部分
    if(len % 2 == 0){
      for(int i = 40; i < len ; i += 2){
        to_do_list.push_back((packet[i] << 8) + packet[i + 1]);
      }
    }else{
      for(int i = 40; i < (len - 1); i += 2){
        to_do_list.push_back((packet[i] << 8) + packet[i + 1]);
      }
      to_do_list.push_back((packet[len - 1]) << 8);
    }

    uint32_t new_checksum = 0;
    for(int i = 0; i < to_do_list.size(); i++){
      // 网络转主机
      new_checksum += ntohs(to_do_list[i]);

      while(new_checksum >= (0x1 << 16)){
        new_checksum = (new_checksum >> 16) + (new_checksum % (0x1 << 16));
      }
    }
    new_checksum = ~new_checksum;
    uint16_t ans = new_checksum & 0xffff;

    // 如果计算出的校验和为 0，则需要设置校验和字段为 0xFFFF
    if(ans == 0){
      ans = 0xffff;
    }

    if(ans == checksum_store){
      udp->uh_sum = ans;
      return true;
    }else{
      udp->uh_sum = ans;
      return false;
    }

  } else if (nxt_header == IPPROTO_ICMPV6) {
    // cout << "ICMP" << endl;
    // ICMPv6
    struct icmp6_hdr *icmp =
        (struct icmp6_hdr *)&packet[sizeof(struct ip6_hdr)];
    // length: len-sizeof(struct ip6_hdr)
    // checksum: icmp->icmp6_cksum

    uint16_t checksum_store = icmp->icmp6_cksum;
    icmp->icmp6_cksum = 0;

    vector<uint16_t> to_do_list;
    // 加入源地址和目的地址
    for(int i = 8; i < 40; i += 2){
      uint16_t combine = (packet[i] << 8) + packet[i + 1];
      to_do_list.push_back(combine);
    }
    // 加入 icmp length
    to_do_list.push_back((packet[4] << 8) + packet[5]);

    // 加入 next protocol
    uint16_t next_protocol = 58;
    to_do_list.push_back(next_protocol);

    // 加入 icmp 剩余部分
    if(len % 2 == 0){
      for(int i = 40; i < len ; i += 2){
        to_do_list.push_back((packet[i] << 8) + packet[i + 1]);
      }
    }else{
      for(int i = 40; i < (len - 1); i += 2){
        to_do_list.push_back((packet[i] << 8) + packet[i + 1]);
      }
      to_do_list.push_back((packet[len - 1]) << 8);
    }

    uint32_t new_checksum = 0;
    for(int i = 0; i < to_do_list.size(); i++){
      // 网络转主机
      new_checksum += ntohs(to_do_list[i]);

      while(new_checksum >= (0x1 << 16)){
        new_checksum = (new_checksum >> 16) + (new_checksum % (0x1 << 16));
      }
    }
    new_checksum = ~new_checksum;
    uint16_t ans = new_checksum & 0xffff;

    // 当接受到校验和应该为 0x0000 但实际为 0xFFFF 的情况时，函数返回值设为 true，并将 packet 中的校验和设为 0x0000
    if((ans == 0x0000) && (checksum_store == 0xffff)){
      return true;
    }

    if(ans == checksum_store){
      icmp->icmp6_cksum = ans;
      return true;
    }else{
      icmp->icmp6_cksum = ans;
      return false;
    }

  } else {
    assert(false);
  }
  return true;
}
