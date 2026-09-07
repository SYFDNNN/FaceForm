# Data

Raw training and testing images are local-only assets and are ignored by Git because of their size and dataset licensing considerations.

Expected local layout:

```text
data/raw/FaceShape-Dataset/
├── training_set/<class>/*.jpg
└── testing_set/<class>/*.jpg
```

The five class folders are `Heart`, `Oblong`, `Oval`, `Round`, and `Square`. Do not commit private, licensed, or personally identifiable images.
