from gradio_client import Client

def formatter(text):
    client = Client("http://127.0.0.1:7860/", verbose=False)
    result = client.predict(
        text,  # str  in '输入文本内容' Textbox component
        "alice",  # str (Option from: [('alice', 'alice')]) in 'Speaker' Dropdown component
        fn_index=5
    )
    return result

def get_audio_from_gradio(raw_text):
    client = Client("http://127.0.0.1:7860/")
    text = formatter(raw_text)
    result = client.predict(
        text,  # str  in '输入文本内容' Textbox component
        "alice",  # str (Option from: [('alice', 'alice')]) in 'Speaker' Dropdown component
        0.5,  # int | float (numeric value between 0 and 1) in 'SDP Ratio' Slider component
        0.6,  # int | float (numeric value between 0.1 and 2) in 'Noise' Slider component
        0.9,  # int | float (numeric value between 0.1 and 2) in 'Noise_W' Slider component
        1,  # int | float (numeric value between 0.1 and 2) in 'Length' Slider component
        "mix",
        # str (Option from: [('ZH', 'ZH'), ('JP', 'JP'), ('EN', 'EN'), ('mix', 'mix'), ('auto', 'auto')]) in 'Language' Dropdown component
        "",
        # str (filepath on your computer (or URL) of file) in 'Audio prompt' Audio component
        "",  # str  in 'Text prompt' Textbox component
        "",  # str  in 'Prompt Mode' Radio component
        "",  # str  in '辅助文本' Textbox component
        0,  # int | float (numeric value between 0 and 1) in 'Weight' Slider component
        fn_index=0
    )
    return result

if __name__ == "__main__":
    status, result = get_audio_from_gradio("老师您好")
    print(result)