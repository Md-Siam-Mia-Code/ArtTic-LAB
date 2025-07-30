# ui.py
import gradio as gr

ASPECT_RATIOS_SD15 = {"1:1": (512, 512), "4:3": (576, 448), "3:2": (608, 416), "16:9": (672, 384)}
ASPECT_RATIOS_SD2 = {"1:1": (768, 768), "4:3": (864, 640), "3:2": (960, 640), "16:9": (1024, 576)}
ASPECT_RATIOS_SDXL = {"1:1": (1024, 1024), "4:3": (1152, 896), "3:2": (1216, 832), "16:9": (1344, 768)}

def create_ui(available_models, schedulers_list, handlers):
    with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as app:
        gr.Markdown("# 🎨 ArtTic-LAB")
        gr.Markdown("v1.1: The Performance & Power Update")

        with gr.Tabs():
            with gr.TabItem("Generate"):
                with gr.Row():
                    with gr.Column(scale=2):
                        status_text = gr.Textbox(label="Status", value="No model loaded.", interactive=False)
                        model_dropdown = gr.Dropdown(label="Model", choices=available_models, value=None)
                        with gr.Row():
                            load_model_btn = gr.Button("Load Model", variant="primary")
                            refresh_models_btn = gr.Button("🔄 Refresh Models")
                        
                        prompt = gr.Textbox(label="Prompt", value="photo of a beautiful woman, 8k, ultra realistic, cinematic", lines=3)
                        negative_prompt = gr.Textbox(label="Negative Prompt", placeholder="e.g., ugly, deformed, blurry", lines=2)
                        
                        with gr.Accordion("Advanced Options", open=False):
                            scheduler_dropdown = gr.Dropdown(label="Sampler", choices=schedulers_list, value=schedulers_list[0])
                            
                            with gr.Row(equal_height=True):
                                width_slider = gr.Slider(label="Width", minimum=256, maximum=2048, value=512, step=64)
                                swap_dims_btn = gr.Button("↔️", min_width=50, elem_id="swap-button")
                                height_slider = gr.Slider(label="Height", minimum=256, maximum=2048, value=512, step=64)
                            
                            gr.Markdown("Set Resolution (SD1.5 / SD2 / SDXL)")
                            with gr.Row():
                                aspect_1_1 = gr.Button("1:1")
                                aspect_4_3 = gr.Button("4:3")
                                aspect_3_2 = gr.Button("3:2")
                                aspect_16_9 = gr.Button("16:9")
                        
                        with gr.Row():
                            steps = gr.Slider(label="Steps", minimum=1, maximum=100, value=30, step=1)
                            guidance = gr.Slider(label="Guidance Scale", minimum=1, maximum=20, value=7.5, step=0.1)
                        with gr.Row():
                            seed = gr.Number(label="Seed", value=12345, precision=0)
                            randomize_seed_btn = gr.Button("🎲", min_width=50)
                        generate_btn = gr.Button("Generate", variant="primary")
                        
                    with gr.Column(scale=3):
                        output_image = gr.Image(label="Result", type="pil", interactive=False, show_label=False)
                        info_text = gr.Textbox(label="Info", interactive=False)

            with gr.TabItem("Gallery"):
                gallery = gr.Gallery(label="Your Generations", show_label=False, columns=5)
                refresh_gallery_btn = gr.Button("Refresh Gallery")

        def set_aspect_ratio(ratio_key, status_str):
            if "SDXL" in status_str:
                ratios, default_res = ASPECT_RATIOS_SDXL, (1024, 1024)
            elif "SD 2.x" in status_str:
                ratios, default_res = ASPECT_RATIOS_SD2, (768, 768)
            else:
                ratios, default_res = ASPECT_RATIOS_SD15, (512, 512)
            
            width, height = ratios.get(ratio_key, default_res)
            return width, height

        aspect_1_1.click(fn=lambda s: set_aspect_ratio("1:1", s), inputs=[status_text], outputs=[width_slider, height_slider])
        aspect_4_3.click(fn=lambda s: set_aspect_ratio("4:3", s), inputs=[status_text], outputs=[width_slider, height_slider])
        aspect_3_2.click(fn=lambda s: set_aspect_ratio("3:2", s), inputs=[status_text], outputs=[width_slider, height_slider])
        aspect_16_9.click(fn=lambda s: set_aspect_ratio("16:9", s), inputs=[status_text], outputs=[width_slider, height_slider])

        refresh_models_btn.click(fn=handlers["refresh_models"], outputs=model_dropdown)
        swap_dims_btn.click(fn=handlers["swap_dims"], inputs=[width_slider, height_slider], outputs=[width_slider, height_slider])
        randomize_seed_btn.click(fn=handlers["randomize_seed"], outputs=seed)
        
        load_model_btn.click(fn=handlers["load_model"], inputs=[model_dropdown, scheduler_dropdown], outputs=[status_text, width_slider, height_slider], show_progress="full")
        generate_btn.click(fn=handlers["generate_image"], inputs=[prompt, negative_prompt, steps, guidance, seed, width_slider, height_slider], outputs=[output_image, info_text]).then(fn=handlers["get_gallery"], outputs=gallery)
        refresh_gallery_btn.click(fn=handlers["get_gallery"], outputs=gallery)

    return app