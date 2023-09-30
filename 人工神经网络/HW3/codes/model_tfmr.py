from turtle import position
import torch
import torch.nn as nn
from torch.nn import CrossEntropyLoss
import torch.nn.functional as F

ACT2FN = {
    "relu": F.relu,
    "tanh": torch.tanh,
    "linear": lambda x: x,
    "sigmoid": torch.sigmoid,
    "gelu": F.gelu,
}

class TransposeLinear(nn.Module):
    def __init__(self, nf, nx):
        super().__init__()
        self.nf = nf
        w = torch.empty(nx, nf)
        nn.init.normal_(w, std=0.02)
        self.weight = nn.Parameter(w)
        self.bias = nn.Parameter(torch.zeros(nf))

    def forward(self, x):
        size_out = x.size()[:-1] + (self.nf,)
        x = torch.addmm(self.bias, x.view(-1, x.size(-1)), self.weight)
        x = x.view(*size_out)
        return x

class TfmrAttention(nn.Module):
    def __init__(self, config):
        super().__init__()

        max_positions = config.max_position_embeddings
        self.register_buffer(
            "bias",
            # TODO START
            # define the bias term for constructing the causal mask (i.e., seeing only prefix tokens).

            # breakpoint()

            # 下三角矩阵
            torch.tril(torch.ones((max_positions, max_positions), dtype=torch.uint8)).reshape(1, 1, max_positions, max_positions),

            # TODO END
        )
        self.register_buffer("masked_bias", torch.tensor(-1e4))

        self.embed_dim = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.embed_dim // self.num_heads
        self.split_size = self.embed_dim
        if self.head_dim * self.num_heads != self.embed_dim:
            raise ValueError(
                f"`embed_dim` must be divisible by num_heads (got `embed_dim`: {self.embed_dim} and `num_heads`: {self.num_heads})."
            )

        self.scale_attn_weights = config.scale_attn_weights
        self.c_attn = TransposeLinear(3 * self.embed_dim, self.embed_dim)
        self.c_proj = TransposeLinear(self.embed_dim, self.embed_dim)

        self.attn_dropout = nn.Dropout(config.attn_pdrop)
        self.resid_dropout = nn.Dropout(config.resid_pdrop)

        self.pruned_heads = set()

    def _attn(self, query, key, value):
        # TODO START
        # implement the multi-head mask self-attnetion mechanism

        # breakpoint()
        # d = 64
        # query = [32, 12, 36, 64]
        key_for_query = key.transpose(-1, -2)
        attn_weights = torch.matmul(query, key_for_query)

        # 除以 根号 d
        if self.scale_attn_weights:
            attn_weights = attn_weights / (float(value.size(-1)) ** 0.5)

        # 从下三角矩阵中截取一部分
        # causal_mask = [1, 1, 36, 36]

        query_length = query.shape[-2]
        key_length = key.shape[-2]

        causal_mask = self.bias[:, :, key_length - query_length : key_length, :key_length].bool()

        # where (condition, x, y)
        attn_weights = torch.where(causal_mask, attn_weights, self.masked_bias.to(attn_weights.dtype))

        # 概率归一化
        attn_weights = nn.Softmax(dim=-1)(attn_weights)
        # drop out 
        attn_weights = self.attn_dropout(attn_weights)

        attention_result = torch.matmul(attn_weights, value)

        return attention_result, attn_weights
        # TODO END

    def _split_heads(self, tensor, num_heads, attn_head_size):
        # TODO START
        # Splits hidden_size dim into attn_head_size and num_heads

        # [batch size, seq length, feature dim]
        # tensor = [32, 36, 768]

        bs = tensor.shape[0]
        seq_len = tensor.shape[1]
        # split head here
        ret_shape = (bs, seq_len, num_heads, attn_head_size)
        # breakpoint()
        tensor = tensor.reshape(*ret_shape)

        # change head to front
        # (batch, head, seq_length, head_features)
        output = tensor.permute(0, 2, 1, 3)
        return output  

        # TODO END

    def _merge_heads(self, tensor, num_heads, attn_head_size):
        # TODO START
        # Merges attn_head_size dim and num_attn_heads dim into hidden_size

        # view 不会改变实际存储方式
        # congtiguous 彻底改变空间结构
        # reshape

        # change sequence to [batch size, seq len, heads, head feature]
        tensor = tensor.permute(0, 2, 1, 3).contiguous()

        bs = tensor.shape[0]
        seq_len = tensor.shape[1]

        new_shape = (bs, seq_len, num_heads * attn_head_size,)

        # [batch size, seq len, total dimension]
        output = tensor.reshape(new_shape)

        return output

        # TODO END

    def forward(
        self,
        hidden_states,
        layer_past=None,
        use_cache=False,
    ):
        query, key, value = self.c_attn(hidden_states).split(self.split_size, dim=2)
        query = self._split_heads(query, self.num_heads, self.head_dim)
        key = self._split_heads(key, self.num_heads, self.head_dim)
        value = self._split_heads(value, self.num_heads, self.head_dim)

        if layer_past is not None:
            past_key, past_value = layer_past
            key = torch.cat((past_key, key), dim=-2)
            value = torch.cat((past_value, value), dim=-2)

        if use_cache is True:
            present = (key, value)
        else:
            present = None

        attn_output, attn_weights = self._attn(query, key, value)

        attn_output = self._merge_heads(attn_output, self.num_heads, self.head_dim)
        attn_output = self.c_proj(attn_output)
        attn_output = self.resid_dropout(attn_output)

        outputs = (attn_output, present)
        outputs += (attn_weights,)

        return outputs  # a, present, (attentions)


class TfmrMLP(nn.Module):
    def __init__(self, intermediate_size, config):
        super().__init__()
        embed_dim = config.hidden_size
        self.c_fc = TransposeLinear(intermediate_size, embed_dim)
        self.c_proj = TransposeLinear(embed_dim, intermediate_size)
        self.act = ACT2FN[config.activation_function]
        self.dropout = nn.Dropout(config.resid_pdrop)

    def forward(self, hidden_states):
        hidden_states = self.c_fc(hidden_states)
        hidden_states = self.act(hidden_states)
        hidden_states = self.c_proj(hidden_states)
        hidden_states = self.dropout(hidden_states)
        return hidden_states


class TfmrBlock(nn.Module):
    def __init__(self, config):
        super().__init__()
        hidden_size = config.hidden_size
        inner_dim = config.n_inner if config.n_inner is not None else 4 * hidden_size

        self.ln_1 = nn.LayerNorm(hidden_size, eps=config.layer_norm_epsilon)
        self.attn = TfmrAttention(config)
        self.ln_2 = nn.LayerNorm(hidden_size, eps=config.layer_norm_epsilon)
        self.mlp = TfmrMLP(inner_dim, config)

    def forward(
        self,
        hidden_states,
        layer_past=None,
        use_cache=False,
    ):
        residual = hidden_states
        hidden_states = self.ln_1(hidden_states)
        attn_outputs = self.attn(
            hidden_states,
            layer_past=layer_past,
            use_cache=use_cache,
        )
        attn_output = attn_outputs[0]  # output_attn: a, present, (attentions)
        outputs = attn_outputs[1:]

        # TODO START
        # Bulid connecetions of different modules in the Tranformer block

        # residual connection
        hidden_states = attn_output + residual
        residual = hidden_states

        # layer norm here
        hidden_states = self.ln_2(hidden_states)

        # residual connection
        hidden_states = residual + self.mlp(hidden_states)

        # TODO END

        if use_cache:
            outputs = (hidden_states,) + outputs
        else:
            outputs = (hidden_states,) + outputs[1:]

        return outputs


class TfmrModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.embed_dim = config.hidden_size

        self.wte = nn.Embedding(config.vocab_size, self.embed_dim)
        self.wpe = nn.Embedding(config.max_position_embeddings, self.embed_dim)

        self.drop = nn.Dropout(config.embd_pdrop)
        self.h = nn.ModuleList([TfmrBlock(config) for _ in range(config.num_hidden_layers)])
        self.ln_f = nn.LayerNorm(self.embed_dim, eps=config.layer_norm_epsilon)

    def get_input_embeddings(self):
        return self.wte

    def forward(
        self,
        input_ids,
        past_key_values=None,
        use_cache=None,
    ):
        input_shape = input_ids.size()
        input_ids = input_ids.view(-1, input_shape[-1])

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        inputs_embeds = self.wte(input_ids)
        # TODO START
        # Implement the positional embeddings. Note that the length of cache hidden states used during inference

        if past_key_values:
            past_length = past_key_values[0][0].shape[-2]
        else:
            past_length = 0
            past_key_values = tuple([None] * len(self.h))

        # breakpoint()

        # input shape = [32, 36]
        seq_len = input_shape[-1]
        start = past_length
        end = past_length + seq_len

        position_ids = torch.arange(start, end, dtype=torch.long, device=device)
        # position_ids = [36]
        # breakpoint()
        position_ids_expand = position_ids.unsqueeze(0)

        position_ids = position_ids_expand.reshape(-1, seq_len)
        position_embeds = self.wpe(position_ids)

        # TODO END
        hidden_states = inputs_embeds + position_embeds

        hidden_states = self.drop(hidden_states)

        output_shape = input_shape + (hidden_states.size(-1),)

        presents = () if use_cache else None
        all_self_attentions = ()
        all_cross_attentions = ()
        all_hidden_states = ()
        for i, (block, layer_past) in enumerate(zip(self.h, past_key_values)):
            all_hidden_states = all_hidden_states + (hidden_states,)
            outputs = block(
                hidden_states,
                layer_past=layer_past,
                use_cache=use_cache,
            )

            hidden_states = outputs[0]
            if use_cache is True:
                presents = presents + (outputs[1],)

            all_self_attentions = all_self_attentions + (outputs[2 if use_cache else 1],)

        hidden_states = self.ln_f(hidden_states)

        hidden_states = hidden_states.view(*output_shape)
        # Add last hidden state
        all_hidden_states = all_hidden_states + (hidden_states,)

        return {
            "last_hidden_state": hidden_states,
            "past_key_values": presents,
            "hidden_states": all_hidden_states,
            "attentions": all_self_attentions,
            "cross_attentions": all_cross_attentions,
        }


class TfmrLMHeadModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.transformer = TfmrModel(config)
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

    def forward(
        self,
        input_ids,
        past_key_values=None,
        labels=None,
        use_cache=None,
        PAD_ID=None,
    ):
        transformer_outputs = self.transformer(
            input_ids=input_ids,
            past_key_values=past_key_values,
            use_cache=use_cache,
        )
        hidden_states = transformer_outputs["last_hidden_state"]
        lm_logits = self.lm_head(hidden_states)

        loss = None
        if labels is not None:
            ce_loss_fct = CrossEntropyLoss(reduction="none")
            # TODO START
            # Implement the loss function. Note that you should shift logits so that tokens < n predict n
            
            # lm_logits = [32, 36, 50257], ignore the end of sentence
            logits_no_eos = lm_logits[..., :-1, :].contiguous()
            # label = [32, 36], ignore the begin of sentence
            labels_no_bos = labels[..., 1:].contiguous()

            # breakpoint()
            bs = labels_no_bos.shape[0]

            pad_pos = torch.eq(labels_no_bos, PAD_ID).to(torch.float).to(labels.device)

            # breakpoint()
            pad_pos = torch.cat([torch.zeros([bs, 1]).to(labels.device), pad_pos[:, :-1]], 1)

            loss_mask = 1. - pad_pos

            dict_len = logits_no_eos.shape[-1]
            logits_for_loss = logits_no_eos.reshape(-1, dict_len)
            labels_for_loss = labels_no_bos.view(-1)

            loss = ce_loss_fct(logits_for_loss, labels_for_loss)
            loss = torch.mean(torch.sum(loss.view(labels_no_bos.size()[0], -1) * loss_mask, 1) / (torch.sum(loss_mask, 1) + 1e-20))
            
            # TODO END

        return {
            "loss": loss,
            "logits": lm_logits,
            "past_key_values": transformer_outputs["past_key_values"],
            "hidden_states": transformer_outputs["hidden_states"],
            "attentions": transformer_outputs["attentions"],
            "cross_attentions": transformer_outputs["cross_attentions"],
         }
        

    def inference(self, device, PAD_ID, batch_size, maxlen, decode_strategy, temperature, top_p=1.0, top_k=50267):
        self.eval()
        allgen = []
        with torch.no_grad():
            for i in range(0, int(5000/batch_size)+1):
                input_ids = torch.tensor([[PAD_ID] for _ in range(batch_size)]).to(device)
                past_key_values = None
                output_ids = input_ids
                for _ in range(maxlen):
                    outputs = self(input_ids, past_key_values=past_key_values, use_cache=True)
                    logits = outputs["logits"]
                    past_key_values = outputs["past_key_values"]
                    logits = logits[:, -1, :] / temperature

                    if decode_strategy == "top-p":
                        # TODO START
                        # implement top-p sampling
                        
                        # 排序
                        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                        # 向左堆积求和
                        predict_prob = F.softmax(sorted_logits, dim=-1)
                        cumulative_probs = torch.cumsum(predict_prob, dim=-1)

                        # Remove tokens with cumulative probability above the threshold
                        sorted_indices_to_remove = cumulative_probs > top_p
                        # 防止一个也选不中的情况
                        sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()
                        sorted_indices_to_remove[:, 0] = 0

                        bs = logits.shape[0]
                        dict_len = logits.shape[1]
                        # 构造一维偏移量
                        seq = torch.arange(bs, device=device, dtype=torch.long)
                        seq_single = seq.unsqueeze(-1)
                        seq = seq_single * dict_len

                        sorted_indices_single = (sorted_indices + seq)

                        indices_to_remove = torch.masked_select(sorted_indices_single, sorted_indices_to_remove)
                        # change into dimension 1
                        logits_single = logits.reshape(-1)
                        logits = torch.index_fill(logits_single, 0, indices_to_remove, -float("inf"))
                        logits = logits.reshape(bs, dict_len)

                        # TODO END
                    elif decode_strategy == "top-k":
                        # TODO START
                        # implement top-k sampling

                        # 排序
                        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                        bs = logits.shape[0]
                        dict_len = logits.shape[1]

                        # 构造一维偏移量
                        seq = torch.arange(bs, device=device, dtype=torch.long)
                        seq_single = seq.unsqueeze(-1)
                        seq = seq_single * dict_len

                        # 转换indices
                        sorted_indices_single = (sorted_indices + seq)
                        index_to_remove = sorted_indices[...,top_k:]
                        index_to_remove = index_to_remove.reshape(-1)

                        logits_single = logits.reshape(-1)
                        
                        logits_single = torch.index_fill(logits_single, 0, index_to_remove, -float("inf"))

                        logits = logits_single.reshape(bs, dict_len)


                        # TODO END
                    prob = logits.softmax(dim=-1) # shape: (batch_size, num_vocabs)
                    now_token = torch.multinomial(prob, 1)[:, :1] # shape: (batch_size)

                    output_ids = torch.cat([output_ids, now_token], 1)
                    input_ids = now_token
                allgen += output_ids.cpu().numpy().tolist()
        pro_allgen = []
        for gen in allgen[:5000]:
            pro_allgen.append([])
            for idx in gen[1:]:
                if idx == PAD_ID:
                    break
                pro_allgen[-1].append(idx)
        self.train() # return to training mode
        return pro_allgen
                