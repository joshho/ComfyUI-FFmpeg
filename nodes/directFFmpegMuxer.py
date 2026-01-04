import os
import subprocess
import folder_paths
import time

class DirectFFmpegMuxer:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_path": ("STRING", {"default": ""}),
                "audio_path": ("STRING", {"default": ""}),
                "pre_delay": ("FLOAT", {"default": 2.0, "min": 0.0, "step": 0.1}),
                "post_delay": ("FLOAT", {"default": 1.0, "min": 0.0, "step": 0.1}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "custom_output_path": ("STRING", {"default": "default"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    OUTPUT_NODE = True 
    FUNCTION = "mux_video"
    CATEGORY = "🔥FFmpeg"

    def mux_video(self, image_path, audio_path, pre_delay, post_delay, filename_prefix, custom_output_path):
        # 1. Determine Output Directory
        if custom_output_path.lower() == "default" or custom_output_path.strip() == "":
            output_dir = folder_paths.get_output_directory()
        else:
            output_dir = os.path.abspath(custom_output_path)
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 2. Replicating your suite's set_file_name logic with Prefix + Timestamp
        timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
        file_name = f"{filename_prefix}_{timestamp}.mp4"
        full_output_path = os.path.normpath(os.path.join(output_dir, file_name))

        # 3. Build FFmpeg Command
        # This handles the 2s delay at start and 1s pad at end via filter_complex
        delay_ms = int(pre_delay * 1000)
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-i', audio_path,
            '-filter_complex', f'[1:a]adelay={delay_ms}|{delay_ms},apad=pad_dur={post_delay}[a]',
            '-map', '0:v', '-map', '[a]',
            '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-shortest',
            full_output_path
        ]

        try:
            # Run without shell for security, capturing output for debugging
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 4. Return for API consumption
            # 'ui' dictionary sends 'text' to the history/$promptid JSON outputs
            return {
                "ui": {"text": [full_output_path]}, 
                "result": (full_output_path,)
            }
        except subprocess.CalledProcessError as e:
            err = e.stderr if e.stderr else "FFmpeg failed to process"
            return {
                "ui": {"text": [f"Error: {err}"]}, 
                "result": (f"Error: {err}",)
            }
