# ui.py
import gradio as gr

def create_ui(available_models, schedulers_list, handlers):
    with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as app:
        gr.Markdown("# 🎨 ArtTic-LAB")
        gr.Markdown("v1.0.0: The Official Release")

        with gr.Tabs():
            with gr.TabItem("Generate"):
                with gr.Row():
                    with gr.Column(scale=2):
                        status_text = gr.Textbox(label="Status", value="No model loaded. Please select and load a model.", interactive=False)
                        model_dropdown = gr.Dropdown(label="Model", choices=available_models, value=None)
                        with gr.Row():
                            load_model_btn = gr.Button("Load Model", variant="primary")
                            refresh_models_btn = gr.Button("🔄 Refresh Models") # NEW BUTTON
                        
                        prompt = gr.Textbox(label="Prompt", value="photo of a beautiful woman, 8k, ultra realistic, cinematic", lines=3)
                        negative_prompt = gr.Textbox(label="Negative Prompt", placeholder="e.g., ugly, deformed, blurry", lines=2)
                        
                        with gr.Accordion("Advanced Options", open=False):
                            scheduler_dropdown = gr.Dropdown(label="Sampler", choices=schedulers_list, value=schedulers_list[0])
                            width_slider = gr.Slider(label="Width", minimum=256, maximum=2048, value=512, step=64)
                            height_slider = gr.Slider(label="Height", minimum=256, maximum=2048, value=512, step=64)
                        
                        with gr.Row():
                            steps = gr.Slider(label="Steps", minimum=1, maximum=100, value=30, step=1)
                            guidance = gr.Slider(label="Guidance Scale", minimum=1, maximum=20, value=7.5, step=0.1)
                        with gr.Row():
                            seed = gr.Number(label="Seed", value=12345, precision=0)
                            randomize_seed_btn = gr.Button("🎲")
                        generate_btn = gr.Button("Generate", variant="primary")
                        
                    with gr.Column(scale=3):
                        output_image = gr.Image(label="Result", type="pil", interactive=False, show_label=False)
                        info_text = gr.Textbox(label="Info", interactive=False)

            with gr.TabItem("Gallery") as gallery_tab:
                gallery = gr.Gallery(label="Your Generations", show_label=False, elem_id="gallery", columns=5)
                refresh_gallery_btn = gr.Button("Refresh Gallery")

        # --- Event Handlers ---
        refresh_models_btn.click(fn=handlers["refresh_models"], outputs=model_dropdown)
        
        load_model_btn.click(
            fn=handlers["load_model"], inputs=[model_dropdown, scheduler_dropdown],
            outputs=[status_text, width_slider, height_slider], show_progress="full"
        )
        generate_btn.click(
            fn=handlers["generate_image"],
            inputs=[prompt, negative_prompt, steps, guidance, seed, width_slider, height_slider],
            outputs=[output_image, info_text]
        ).then(fn=handlers["get_gallery"], outputs=gallery)

        refresh_gallery_btn.click(fn=handlers["get_gallery"], outputs=gallery)
        gallery_tab.select(fn=handlers["get_gallery"], outputs=gallery)
        randomize_seed_btn.click(fn=lambda: -1, inputs=[], outputs=seed)
        
    return app