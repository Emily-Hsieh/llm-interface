import ollama
import gradio as gr
import time

model_type = ['全部', '多模態', '純文字']
model_list1 = ['llama3.2-vision:latest', 'bakllava:latest', 'llava:latest']
model_list2 = ['qwen2.5:latest', 'deepseek-r1:latest', 'granite3-dense:8B', 'mistral:latest']
model_list = model_list1 + model_list2

def model_list_adjust(main_choice):
    if main_choice == '多模態':
        return gr.update(choices = model_list1)
    elif main_choice == '純文字':
        return gr.update(choices = model_list2)
    else:
        return gr.update(choices = model_list)

def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)

def add_message(is_continute, history, message):
    if is_continute == '單次問答':
        history = []
    if message["text"] is not None:
        history.append({"role": "user", "content": message["text"]})
        for x in message["files"]:
            history.append({"role": "user", "content": {"path": x}})
    else:
        for x in message["files"]:
            history.append({"role": "user", "content": {"path": x}})
    return history, gr.MultimodalTextbox(value=None, interactive=False)

def bot(select_model, history: list):
    adjust_history = []
    for item in history:
        content = item['content']
        if isinstance(content, tuple) and len(content) == 1:
            adjust_history.append({"role": "assistant", "images": [content[0]]})
        else:
            adjust_history.append({"role": "assistant", "content": content})
    response = ollama.chat(
            model = select_model,
            messages = adjust_history
        )
    history.append({"role": "assistant", "content": ""})
    for character in response['message']['content']:
        history[-1]["content"] += character
        time.sleep(0.05)
        yield history


with gr.Blocks() as demo:
    gr.Markdown("## 大型語言模型的地端嘗試介面。")
    gr.Markdown("1. 請選擇要使用的模型：")
    model_type_selector = gr.Radio(model_type, value = "全部")
    model_selector = gr.Radio(model_list)   
    model_type_selector.change(model_list_adjust, model_type_selector, model_selector)
    feedback_type = gr.Radio(['單次問答', '多輪問答'], value = '單次問答') 



    gr.Markdown("2. 以下為嘗試頁面。請注意如果重新輸入提問則先前的問答將會被覆蓋：")
    chatbot = gr.Chatbot(elem_id="對話機器人", bubble_full_width=False, type="messages")

    chat_input = gr.MultimodalTextbox(
        interactive=True,
        file_count="multiple",
        placeholder="輸入文字或上傳文件...",
        show_label=False,
        sources=["microphone", "upload"],
    )

    chat_msg = chat_input.submit(
        add_message, [feedback_type, chatbot, chat_input], [chatbot, chat_input]
    )
    bot_msg = chat_msg.then(bot, [model_selector, chatbot], chatbot, api_name="bot_response")
    bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input])

    chatbot.like(print_like_dislike, None, None, like_user_message=True)

if __name__ == "__main__":
    demo.launch()