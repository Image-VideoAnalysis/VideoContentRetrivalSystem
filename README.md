# Video Retrieval System

This project is a visual content analysis tool developed for the course "Image and Video Analysis with Deep Learning".

## Features

-   **Shot Boundary Detection**:  TransNetV2 model is used to detect shot boundaries in videos.
-   **Keyframe Extraction**: For each shot, a keyframe is extracted to represent the content of the shot.
-   **Image-Text Similarity**: An OpenAI's CLIP model computes the similarity between your text query and the extracted keyframes.
-   **Vector Search**: Faiss lets perform efficient similarity search on the CLIP image embeddings.
-   **Web Interface**: A web interface built with Svelte and FastAPI is provided to interact with the system.

## Project Structure

The project is divided into a backend and a frontend.

-   **Backend**: The backend is responsible for processing videos, extracting keyframes, and performing the similarity search. It is built with Python and FastAPI.
-   **Frontend**: The frontend provides a user interface to upload videos and search for them using text queries. It is built with Svelte.

## Data Setup

### For Inference (Video Search)
To run the system in inference mode and search the pre-existing dataset, you **must** place the `V3C1_200` video dataset folder into `src/Frontend/static/videos/`. This allows the web interface to retrieve and display the correct videos from search results.

### For Processing New Videos (Shot Boundary Detection)
If you need to run the shot boundary detection on new videos, you must place a `Dataset` folder at the project's root directory. This folder should contain the new videos you wish to process. This step is **only** necessary for analyzing new content, not for searching the existing dataset.

## Installation

There are two recommended ways to set up the backend environment: using Conda (recommended for easier dependency management) or using a standard Python virtual environment with pip.

### Option 1: Using Conda

1.  **Create a Conda environment**:

    This is the recommended method as it handles complex dependencies like PyTorch and Faiss automatically. Choose the file for your operating system:

    ```bash
    # For macOS
    conda env create -f environments/environment_macOS.yml

    # For Windows
    conda env create -f environments/environment_windows.yml
    ```

2.  **Activate the Conda environment**:
    -   **macOS/Linux**:
        ```bash
        conda activate VCA-env
        ```
    -   **Windows**:
        ```bash
        conda activate VCA-env
        ```

### Option 2: Using Pip and Venv

This method is an alternative to Conda and uses standard Python tools.

1.  **Create a Python Virtual Environment**:

    From the root of the project, run:
    ```bash
    python3 -m venv venv
    ```

2.  **Activate the virtual environment**:
    -   **macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```
    -   **Windows (Command Prompt)**:
        ```bash
        .\venv\Scripts\activate.bat
        ```
    -   **Windows (PowerShell)**:
        ```bash
        .\venv\Scripts\Activate.ps1
        ```

3.  **Install dependencies**:

    Once the environment is activated, install the required packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    **Note**: This method might require you to manually resolve system-level dependencies if you encounter errors with packages like PyTorch or Faiss.

### Frontend

1.  **Navigate to the frontend directory**:
    ```bash
    cd src/Frontend
    ```
2.  **Install the dependencies**:
    ```bash
    npm install
    ```

### System-Level Dependencies

#### FFmpeg

The Shot Boundary Detection feature relies on the `ffmpeg` command-line tool. If you intend to use this feature, you must have `ffmpeg` installed on your system. However, if you only plan to use the application for inference (i.e., searching for videos), you do not need to install it.

-   **macOS (using Homebrew)**:
    ```bash
    brew install ffmpeg
    ```
-   **Windows and Linux**:
    Please refer to the official FFmpeg website for installation instructions: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Usage

1.  **Start the backend**:

    ```bash
    fastapi dev backend.py
    ```

    or

    ```bash
    uvicorn backend:app --reload
    ```

2.  **Start the frontend**:

    ```bash
    npm run dev
    ```

3.  **Open your browser** and navigate to `http://localhost:5173`.

## Troubleshooting

### macOS Error: OMP: Error #15

If you encounter the following error on macOS when starting the backend:

```
OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
OMP: Hint This means that multiple copies of the OpenMP runtime have been linked into the program. That is dangerous, since it can degrade performance or cause incorrect results. The best thing to do is to ensure that only a single OpenMP runtime is linked into the process, e.g. by avoiding static linking of the OpenMP runtime in any library. As an unsafe, unsupported, undocumented workaround you can set the environment variable KMP_DUPLICATE_LIB_OK=TRUE to allow the program to continue to execute, but that may cause crashes or silently produce incorrect results. For more information, please see http://openmp.llvm.org/
zsh: abort      fastapi dev backend.py
```

One known workaround is starting the backend with the following command:

```bash
env KMP_DUPLICATE_LIB_OK=TRUE python src/Backend/backend.py
```

## License

[MIT](https.choosealicense.com/licenses/mit/)
