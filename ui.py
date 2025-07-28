# ui.py
import gradio as gr

def create_ui(available_models, handlers):
    initial_model = available_models[0] if available_models else None
    
    with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as app:
        gr.Markdown("# 🎨 ArtTic-LAB")
        gr.Markdown("v1.0: Stable Release")

        with gr.Tabs():
            with gr.TabItem("Generate"):
                with gr.Row():
                    with gr.Column(scale=2):
                        with gr.Row():
                            model_dropdown = gr.Dropdown(label="Model", choices=available_models, value=initial_model)
                            load_model_btn = gr.Button("Load Model")
                        status_text = gr.Textbox(label="Status", interactive=False, lines=1)
                        prompt = gr.Textbox(label="Prompt", value="photo of a beautiful woman, 8k, ultra realistic, cinematic", lines=3)
                        negative_prompt = gr.Textbox(label="Negative Prompt", placeholder="e.g., ugly, deformed, blurry, cartoon", lines=2)
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

        load_model_btn.click(fn=handlers["load_model"], inputs=[model_dropdown], outputs=[status_text], show_progress="full")
        
        generate_btn.click(
            fn=handlers["generate_image"],
            inputs=[prompt, negative_prompt, steps, guidance, seed],
            outputs=[output_image, info_text]
        ).then(fn=handlers["get_gallery"], outputs=gallery)

        refresh_gallery_btn.click(fn=handlers["get_gallery"], outputs=gallery)
        gallery_tab.select(fn=handlers["get_gallery"], outputs=gallery)
        randomize_seed_btn.click(fn=lambda: -1, inputs=[], outputs=seed)
        
    return app