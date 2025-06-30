# Visual Content Analysis

This project is a visual content analysis tool that allows you to search for videos using natural language queries. It uses a combination of computer vision and natural language processing techniques to understand the content of videos and match it with your search queries.

## Features

-   **Shot Boundary Detection**: The project uses a TransNetV2 model to detect shot boundaries in videos.
-   **Keyframe Extraction**: For each shot, a keyframe is extracted to represent the content of the shot.
-   **Image-Text Similarity**: The project uses OpenAI's CLIP model to compute the similarity between your text query and the extracted keyframes.
-   **Vector Search**: The project uses Faiss to perform efficient similarity search on the CLIP image embeddings.
-   **Web Interface**: The project provides a web interface built with Svelte and FastAPI to interact with the system.

## Project Structure

The project is divided into a backend and a frontend.

-   **Backend**: The backend is responsible for processing videos, extracting keyframes, and performing the similarity search. It is built with Python and FastAPI.
-   **Frontend**: The frontend provides a user interface to upload videos and search for them using text queries. It is built with Svelte.

## Data Setup

At the root level of the project, you need to create a folder named `Dataset`. This folder should contain the videos you want to analyze.

## Installation

### Backend

1.  **Create a Conda environment**:

    ```bash
    conda env create -f environment.yml -p /home/user/anaconda3/envs/env_name
    ```

    There are two environment files available: `environment_mac.yml` for macOS and `environment_windows.yml` for Windows.

2.  **Activate the Conda environment**:

    -   For Windows CMD:

        ```bash
        venv_name\Scripts\activate.bat
        ```

    -   For Windows PowerShell:

        ```bash
        venv_name\Scripts\Activate.ps1
        ```

    -   For Linux/macOS:

        ```bash
        conda activate env_name
        ```

3.  **Install OpenCV**:

    In some cases, the `cv2` library might cause issues. To solve them, try reinstalling it in the Conda environment:

    ```bash
    conda install opencv
    pip install opencv-python
    ```

### Frontend

1.  **Navigate to the frontend directory**:

    ```bash
    cd src/Frontend
    ```

2.  **Install the dependencies**:

    ```bash
    npm install
    ```

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
Ex
## License

[MIT](https.choosealicense.com/licenses/mit/)
