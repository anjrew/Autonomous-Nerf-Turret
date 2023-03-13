conda create -n NERF_TURRET python=3.8
conda activate -n NERF_TURRET
pip install -r requirements.txt
cd /components/camera_vision
curl https://pjreddie.com/media/files/yolov3.weights -o yolov3.weights