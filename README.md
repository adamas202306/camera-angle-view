# camera-angle-view
[Custom node for ComfyUI] Supports adjustment of camera angle and distance.
<p align="center">
  <b>ComfyUI에서 사용 가능한 카메라 앵글 조정 노드입니다.</b><br>
  이미지 생성 시 카메라 뷰파인더를 기준으로 앵글, 360도 방위, 틸팅, 거리 등을 조정합니다.
</p>

## 빠른 시작

ComfyUI가 설치되어 정상 실행되는 환경에서 시작하세요.

※ 초기 개발 버전으로 ComfyUI Manager에서는 검색, 설치가 안됩니다.
1. 소스코드(camera-angle-view)를 내려 받으세요.
2. custom_nodes 안에 압축을 풀고, ComfyUI 를 재시작 하세요.


---

## 워크플로 맵

<img width="1198" height="1127" alt="workflow_ex" src="https://github.com/user-attachments/assets/dc1a6f98-2851-4460-97da-de20456e608f" />


적용 단계는 매우 단순합니다.
Positive Prompt와 함께 사용하며, join strings / Text Concatenate 노드를 이용해 단일 프롬프트로 묶은 뒤 Clip Text Encoding 노드로 입력하시면 됩니다.

### 주요 기능

카메라를 가정하여 촬영 현장에서의 구도/각도/피사체와의 거리 등을 설정할 수 있습니다.

| 기능              | 설명                                                                                                                                                                                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Side-View**   | 피사체를 대상으로 지면부터 상단까지 180° 범위에서 앵글을 설정합니다.<br>*※ 우측 프레임의 '카메라 앵글'과 동기화하며, 카메라를 상-하 조정 시 custom mode 로 처리됩니다.*                                                                                                                                                                 |
| **Top-View**    | 피사체를 정중앙에 놓고 360° 방위각 내에서 카메라의 방향을 설정합니다.<br>※ 이미지 생성 시 해당 모델의 해석 차이로 간혹 좌-우가 반전됩니다. 프롬프트는 카메라 시점을 기준으로 합니다.                                                                                                                                                                |
| **Distance**    | 피사체로부터의 거리를 설정합니다. 0.1 ~ 10m 사이를 1m 단위로 조정 가능합니다. (우측 프레임에 있는 '피사체와의 거리' 는 희망하는 거리를 제한없이 입력하실 수 있습니다.  단, 최소 단위는 10cm 입니다.)                                                                                                                                                 |
| **Dutch Angle** | 카메라 기울기를 좌-우 각 30' 범위에서 조정 가능합니다.<br>※ 카메라 중앙을 누르면 수평 상태로 돌아 옵니다.                                                                                                                                                                                                           |
| **피사체 유형**      | 피사체의 유형은 '인물', '제품', '장소' 로 나뉘며, '인물'과 '장소'는 카메라 높이가 190cm 를 기준으로 설정됩니다.<br>'제품'은 카메라 높이가 20cm 를 기준으로 설정됩니다.                                                                                                                                                                |
| **카메라 앵글**      | 피사체를 바라보는 카메라의 촬영 각도를 조정합니다.<br>카메라를 드래그하여 조정할 수 있으며, 사전 설정된 프리셋은 다음과 같습니다.<br>**Bird-eye-View / High Angle / Slight High Angle / Eye Level / Slight Low Angle / Low Angle / Worm's-eye-View**                                                                              |
| **360°앵글**      | 피사체를 중심에 두고 360° 반경에서 카메라의 촬영 위치를 조정합니다.<br>카메라를 드래그하여 조정할 수 있으며, 사전 설정된 프리셋은 다음과 같습니다.<br>**Front / Front-Right / Right / Rear-Right / Back / Rear-Left / Left / Front-Left**                                                                                              |
| **초점 거리**       | 초점 거리로 표현하였지만 렌즈 구경과 같습니다.<br>사전 설정된 프리셋은 다음과 같습니다.<br>**광각 스냅(24mm-35mm) / 인물 스냅(50mm) / 초광각(20mm) / 망원(70mm-200mm) / 초망원(300mm-500mm)**<br>※ 이미지 생성 프롬프트의 해석 상 ***<font color="#c0504d">투영 공간이 실내이거나 주변에 사물이 있는 것으로 해석되면 '망원', '초망원' 모드는 미적용되는 사례가 있음</font>***을 확인하였습니다. |
| **조리개**         | 카메라로 들어오는 빛의 양을 조정합니다.<br>사전 설정된 프리셋은 다음과 같습니다.<br>**최대 개방(f/1.2-f2.0) / 중간 개방(f/4-f/8) / 조리개 조임(f/11-f/22)**<br>1) '최대 개방'은 야간 촬영, 인물 감성샷, 실내 촬영에 적합합니다.<br>2) '중간 개방'은 Sweet Spot 으로 인물/정물/풍경 스냅 이미지에 적합합니다.<br>3) '조리개 조임'은 대규모 풍경 사진, 가로등 또는 광원의 빛 갈라짐 연출 등에 적합합니다.     |
| **사용자 설정**      | 위 기능항목에서 설정된 값은 각 항목에 표시되며, 직접 수정할 수 있습니다.                                                                                                                                                                                                                                  |
| **배경 흐림**       | 프롬프트에서 특정 오브제에 포커싱 선언을 하지 않는 한 카메라는 피사체를 향하며, 이때 뒷 배경을 흐리게 할 지 선택합니다.<br>- **<font color="#c0504d">RED</font>**: Blur Off<br>- **<font color="#00b050">GREEN</font>**: Blur On                                                                                              |
| **Krea2**       | 카메라 구도 선언 프롬프트를 Krea2 모델에 최적화된 방식으로 제공합니다.                                                                                                                                                                                                                                  |
| **SD/ZTB**      | 카메라 구도 선언 프롬프트를 Stable Diffusion 문법으로 제공합니다.                                                                                                                                                                                                                                |



## 노드 적용 샘플
<p align="center">
  <b>Test Prompt</b><br>
  A girl stands next to a yellow bus wearing a cone hat and holding an umbrella in her hand.
</p>
<img width="1336" height="752" alt="k_0_15" src="https://github.com/user-attachments/assets/bc0b6606-d67a-4b27-97aa-b28ce0d33f8f" />
<img width="1336" height="752" alt="k_0_14" src="https://github.com/user-attachments/assets/3a37cd71-531b-47fa-86b2-3c8f8563a1fd" />
<img width="1336" height="752" alt="k_0_13" src="https://github.com/user-attachments/assets/43679344-e4a9-4920-a7ac-adc981881ace" />
<img width="1336" height="752" alt="k_0_12" src="https://github.com/user-attachments/assets/658eadc0-abb8-4fb6-919b-3bcdf76149d7" />
<img width="1336" height="752" alt="k_0_04" src="https://github.com/user-attachments/assets/cfe73d82-9319-4b28-8a7f-7d0a7b96119e" />
<img width="1336" height="752" alt="k_0_03" src="https://github.com/user-attachments/assets/e52da2b2-5100-4b02-bd3e-4f74fd03496b" />
<img width="1336" height="752" alt="k_0_02" src="https://github.com/user-attachments/assets/25b7c5ca-2562-46f6-8971-6d14109bcf9a" />
<img width="1336" height="752" alt="k_0_01" src="https://github.com/user-attachments/assets/46305545-b953-46ec-87f0-9776e2523de3" />
<img width="1336" height="752" alt="k_0" src="https://github.com/user-attachments/assets/e8d5c6d5-55d0-4e15-9a65-fa6febbac24b" />


## 만든 이유

이 노드들은 ComfyUI를 사용해 이미지 생성 과정에서 화면 구도 조정이 매우 번거롭고, 불편해서 좀더 쉽게 직관적으로 설정할 수 있도록 하기 위해서 만들어졌습니다. 제 노트북 사양이 좋지 못해서 Krea2 에 맞춰 개발한 첫번째 노드입니다. ZTB, Qwen Image, Flux 에도 적용 가능하도록 하였지만 첫 작업이라 예쁘지는 않습니다.

## 라이선스

ACKMAN 소유 노드, 문서, 예시, 워크플로우, 프로젝트 내 에셋 등은 GNU GPL v3.0 (`GPL-3.0-only`)으로 배포됩니다. [GPL-3.0 조건](../LICENSE)에 따라 사용, 학습, 수정, 재배포할 수 있으며 상업적 이용도 가능합니다. 수정본을 배포할 때는 GPL-3.0을 따르고 필요한 라이선스와 저작권 고지를 유지해야 합니다.

외부 모델, 체크포인트, LoRA, 라이브러리, 도구, 서비스는 각각의 라이선스와 이용 조건을 따릅니다. 특정 모델이나 에셋을 사용하거나 그 결과물을 공유·판매하기 전에 해당 조건을 확인하세요.

## 링크

- YouTube: https://www.youtube.com/@heres_ackman
- GitHub: https://github.com/adamas202306/camera-angle-view
