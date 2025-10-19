# R1 Reasoning Dataset Generation 



## QA Pairs Generation

We create a `scene description` by combining the objects (with meta info such as location, depth) using a template. 

We keep the couting relevant questions and add a `How many items are there in the described scene?` question to count all objects in the scene.

Example QA pair:

```json
{'img_filename': 'CLEVR_trainA_048403.png',
  'question': 'How many things are both on the right side of the big yellow rubber thing and left of the purple ball?',
  'answer': '5',
  'description': 'Scene Description:\nA large red rubber cylinder rotated 291.3° located at 3D coordinates (-0.89, -2.73, 0.70) and pixel coordinates (101, 152, 10.04)\nA small purple metal sphere rotated 247.7° located at 3D coordinates (2.93, 0.87, 0.35) and pixel coordinates (379, 183, 9.66)\nA large cyan rubber cylinder rotated 114.5° located at 3D coordinates (-2.40, 2.23, 0.70) and pixel coordinates (246, 82, 13.94)\nA small red metal cylinder rotated 109.9° located at 3D coordinates (-0.95, 1.77, 0.35) and pixel coordinates (270, 113, 12.83)\nA small red rubber cylinder rotated 343.7° located at 3D coordinates (-0.12, -0.74, 0.35) and pixel coordinates (209, 153, 10.82)\nA large red rubber cylinder rotated 324.5° located at 3D coordinates (-2.71, -2.21, 0.70) and pixel coordinates (84, 119, 11.59)\nA small red metal cylinder rotated 1.1° located at 3D coordinates (2.88, -0.12, 0.35) and pixel coordinates (342, 200, 9.12)\nA small gray rubber cube rotated 144.9° located at 3D coordinates (0.79, 0.98, 0.35) and pixel coordinates (299, 145, 11.19)\nA large yellow rubber cube rotated 90.0° located at 3D coordinates (-1.78, -0.31, 0.70) and pixel coordinates (180, 110, 12.05)\n'}
```

See `generate_scene_qa_pairs.ipynb` for details.

## R1 Response Generation

`query_r1.py`: We get the predictions and obtain the reasoning trace of R1 by querying SilconFlow (You can register via https://cloud.siliconflow.cn/i/rYfeQZ6A so both we 20M token credit!)

Example Response:

```json
<think>Okay, let's see. The user is asking how many items are there in the described scene. Let me go through the scene description step by step.

So, the scene description lists each object with details like color, material, shape, rotation, 3D coordinates, and pixel coordinates. Each entry starts with "A" which usually indicates one item each. Let me count each one.

First entry: "A small green metal cylinder..." That's one. Second: "A small blue rubber cylinder..." Second item. Third: "A small cyan rubber cylinder..." That's three. Fourth: "A large cyan metal sphere..." Four. Fifth: "A large brown metal cube..." Five. Sixth: "A large yellow rubber cube..." Six. Seventh: "A large brown rubber cylinder..." That's seven. 

Wait, did I miss any? Let me check again. The list has entries from "A small green..." up to the seventh one. Each sentence starts with "A", which suggests each is a separate item. No commas separating multiple items in a single entry. Each has different attributes and coordinates, so they must all be distinct. 

So the answer should be 7 items.
</think>

There are 7 items in the described scene. Each entry corresponds to one distinct object, listed by their properties, coordinates, and rotations.
```

In `v1` we do not constrain the output format and thus the answers are somewhat messy to parse. We then switched to `v2` by explicitly prompting the model to generate the answer with `**The answer is: **` 

## Reasoning Path Filtering

`filter_r1.py`: We filter out (almost) valid reasoning trace, by juding whether the R1 answer is correct (following our previous work [Math-Shepherd](https://arxiv.org/abs/2312.08935)). 

## HF dataset creation

Finally, we create the dataset using `create_hf_dataset.py` and upload to HF dataset hub.



