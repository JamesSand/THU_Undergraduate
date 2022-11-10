#include "protocol.h"
#include "common.h"
#include "lookup.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include<iostream>
using namespace std;

RipErrorCode disassemble(const uint8_t *packet, uint32_t len,
                         RipPacket *output) {
  // TODO
  // len 是否包括一个的 IPv6 header 的长度。
  if(len < 40){
    return RipErrorCode::ERR_LENGTH;
  }

  // IPv6 Header 中的 Payload Length 加上 Header 长度是否等于 len。
  uint32_t payload_len = (packet[4] << 8) + packet[5];
  if((payload_len + 40) != len){
    return RipErrorCode::ERR_LENGTH;
  }

  // IPv6 Header 中的 Next header 字段是否为 UDP 协议。
  uint8_t next_header = packet[6];
  if(next_header != 17){
    return RipErrorCode::ERR_IP_NEXT_HEADER_NOT_UDP;
  }

  // IPv6 Header 中的 Payload Length 是否包括一个 UDP header 的长度。
  if(payload_len < 8){
    return RipErrorCode::ERR_LENGTH;
  }

  // 检查 UDP 源端口和目的端口是否都为 521。
  uint16_t source_port = (packet[40] << 8) + packet[41];
  uint16_t destination_port = (packet[42] << 8) + packet[43];
  if((source_port != 521) || (destination_port != 521)){
    return RipErrorCode::ERR_BAD_UDP_PORT;
  }

//   检查 UDP header 中 Length 是否等于 UDP header 长度加上 RIPng header
//  * 长度加上 RIPng entry 长度的整数倍。
  uint16_t udp_header_len = (packet[44] << 8) + packet[45];
  if(((udp_header_len - 4 - 8) % sizeof(ripng_entry)) != 0){
    return RipErrorCode::ERR_LENGTH;
  }

//   检查 RIPng header 中的 Command 是否为 1 或 2，
//  * Version 是否为 1，Zero（Reserved） 是否为 0。
  uint8_t rip_command = packet[48];
  uint8_t rip_version = packet[49];
  uint16_t rip_zero = (packet[50] << 8) + packet[51];
  if((rip_command != 1) && (rip_command != 2)){
    return RipErrorCode::ERR_RIP_BAD_COMMAND;
  }
  if(rip_version != 1){
    return RipErrorCode::ERR_RIP_BAD_VERSION;
  }
  if(rip_zero != 0){
    return RipErrorCode::ERR_RIP_BAD_ZERO;
  }

//   对每个 RIPng entry，当 Metric=0xFF 时，检查 Prefix Len
//  * 和 Route Tag 是否为 0。
// 对每个 RIPng entry，当 Metric!=0xFF 时，检查 Metric 是否属于
//  * [1,16]，并检查 Prefix Len 是否属于 [0,128]，是否与 IPv6 prefix 字段组成合法的
//  * IPv6 前缀。
  for(int i = 52; i < len; i += sizeof(ripng_entry)){
    in6_addr rip_ipv6 = {0};
    for(int j = 0; j < 16; j++){
      rip_ipv6.s6_addr[j] = packet[i + j];
    }
    uint16_t rip_route_tag = (packet[i + 16] << 8) + packet[i + 17];
    uint8_t rip_prefix_len = packet[i + 18];
    uint8_t rip_matric = packet[i + 19];
    if(rip_matric == 0xff){
      if(rip_route_tag != 0 ){
        return RipErrorCode::ERR_RIP_BAD_ROUTE_TAG;
      }
      if(rip_prefix_len != 0){
        return RipErrorCode::ERR_RIP_BAD_PREFIX_LEN;
      }
    }else if((1 <= rip_matric) && (rip_matric <= 16)){
      if((rip_prefix_len < 0) || (rip_prefix_len > 128)){
        return RipErrorCode::ERR_RIP_BAD_PREFIX_LEN;
      }
      // 检查是否组成正确 ipv6 前缀
      int valid_nums = rip_prefix_len / 8;
      int residue = rip_prefix_len % 8;
      for(int j = 0; j < 16; j++){
        if(j < valid_nums){
          continue;
        }
        if(j == valid_nums){
          if((rip_ipv6.s6_addr[j] & (0xff >> residue)) != 0x00){
            return RipErrorCode::ERR_RIP_INCONSISTENT_PREFIX_LENGTH;  
          }
        }
        if(j > valid_nums){
          if(rip_ipv6.s6_addr[j] != 0x00){
            return RipErrorCode::ERR_RIP_INCONSISTENT_PREFIX_LENGTH; 
          }
        }
      }


    }else{
      return RipErrorCode::ERR_RIP_BAD_METRIC;
    }
  }

  // 组装成正确的 rip_packet
  output->command = rip_command;
  output->numEntries = (udp_header_len - 4) / sizeof(ripng_entry);
  // 存储所有正确的 entry
  vector<ripng_entry> store;
  for(int i = 52; i < len; i += sizeof(ripng_entry)){
    uint16_t rip_route_tag = (packet[i + 16] << 8) + packet[i + 17];
    rip_route_tag = htons(rip_route_tag);
    uint8_t rip_prefix_len = packet[i + 18];
    uint8_t rip_matric = packet[i + 19];
    ripng_entry temp;
    temp.route_tag = rip_route_tag;
    temp.prefix_len = rip_prefix_len;
    temp.metric = rip_matric;
    for(int j = 0; j < 16; j++){
      temp.prefix_or_nh.s6_addr[j] = packet[i + j];
    }
    store.push_back(temp);
  }
  // 填入 output
  for(int i = 0; i < output->numEntries; i++){
    output->entries[i] = store[i];
  }

  return RipErrorCode::SUCCESS;
}

uint32_t assemble(const RipPacket *rip, uint8_t *buffer) {
  // TODO
  // 报文头部
  // command
  buffer[0] = rip->command;
  // version
  buffer[1] = 1;
  // must zero
  buffer[2] = 0;
  buffer[3] = 0;

  // 每一个 entry
  for(int i = 0; i < rip->numEntries; i++){
    // ipv6 部分
    for(int j = 0; j < 16; j++){
      buffer[i * 20 + 4 + j] = rip->entries[i].prefix_or_nh.s6_addr[j];
    }
    // route tag 部分
    buffer[i * 20 + 4 + 16] = (rip->entries[i].route_tag & 0xff);
    buffer[i * 20 + 4 + 16 + 1] = (rip->entries[i].route_tag >> 8);
    
    // prefix len 部分
    buffer[i * 20 + 4 + 16 + 2] = rip->entries[i].prefix_len;

    // metric 部分
    buffer[i * 20 + 4 + 19] = rip->entries[i].metric;

  }
  

  return (4 + rip->numEntries * 20);
}