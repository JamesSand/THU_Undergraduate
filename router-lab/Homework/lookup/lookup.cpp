#include "lookup.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include<iostream>
#include<typeinfo>
using namespace std;

vector<RoutingTableEntry>RoutingTable;

void update(bool insert, const RoutingTableEntry entry) {
  // TODO
  if(insert == true){
    // 插入
    RoutingTable.push_back(entry);
    return;
  }

  if(insert == false){
    // 删除
    for(int i = 0; i < RoutingTable.size(); i++){
      // 对 IPv6 addr 进行对比
      if((RoutingTable[i].addr == entry.addr) && (RoutingTable[i].len == entry.len)){
        RoutingTable.erase(RoutingTable.begin() + i);
        return;
      }
    }
  }
}

bool prefix_query(const in6_addr addr, in6_addr *nexthop, uint32_t *if_index) {
  // TODO
  // 这里要使用最长前缀匹配
  bool hasmatch = false;
  int max_match = -1;
  int max_index = -1;
  for(int i = 0; i < RoutingTable.size(); i++){
    // 前缀长度
    int prefix_len = RoutingTable[i].len;
    // 地址掩码
    in6_addr mask_code = len_to_mask(prefix_len);
    // 获得路由表项前缀
    in6_addr prefix1 = RoutingTable[i].addr & mask_code;
    // 获得目的地址前缀
    in6_addr prefix2 = addr & mask_code;
    if(prefix1 == prefix2){
      hasmatch = true;
      if(prefix_len >= max_match){
        max_match = prefix_len;
        max_index = i;
      }
    }
  }

  if(hasmatch){
    *nexthop = RoutingTable[max_index].nexthop;
    *if_index = RoutingTable[max_index].if_index;
    return true;
  }

  return false;
}

int mask_to_len(const in6_addr mask) {
  // TODO
  int counter = 0;
  int current_index = 0;
  for(; current_index < 16; current_index++){
    if((mask.s6_addr[current_index] ^ 0xff) == 0x00){
      counter += 8;
    }else{
      break;
    }
  }

  // 如果这时候已经处理了 16 个字节，则直接返回
  if(current_index == 16){
    return counter;
  }

  // 否则继续处理下一个字节
  // 这个字节是 1 0 交界的字节
  int current_postion = 0;
  // 对 1 的部分做校验
  for(; current_postion < 7; current_postion++){
    if((mask.s6_addr[current_index] & (0x80 >> current_postion)) == 0x00){
      break;
    }else{
      counter++;
    }
  }
  
  return counter;
}

in6_addr len_to_mask(int len) {
  // TODO
  in6_addr res = {0};

  // 高位 len/8 个字节置为 0xff
  for(int i = 0; i < (len / 8); i++){
    res.s6_addr[i] = 0xff;
  }

  // 如果已经处理了16个字节，则直接返回
  if((len / 8) == 16){
    return res;
  }

  // 否则处理最后一个字节
  // 设为0xff
  res.s6_addr[(len / 8)] = 0xff;
  // 左移 8 - (len % 8) 位
  for(int i = 0; i < (8 - (len % 8)); i++){
    res.s6_addr[(len / 8)] = (res.s6_addr[(len / 8)] << 1);
  }

  return res;
}
