# CTformer pretrained weights

`T2T_vit_530000iter.ckpt` and `loss_530000_iter.npy` come from CTformer's own
release: <https://github.com/wdayang/CTformer/tree/main/model_pretrained>

## What these are

Despite the `T2T_vit_` name, this is **not** a generic ImageNet T2T-ViT. It is a
CTformer trained on CT: `tokens_to_token.attention1.kqv.weight` is `(192, 49)`,
i.e. a 7x7x**1** grayscale patch — an ImageNet model would be 7x7x3 = 147. The
`loss_530000_iter.npy` beside it is that run's loss curve.

CTformer's README states its training data is the 2016 NIH-AAPM-Mayo Low-Dose CT
Grand Challenge. **These weights are therefore derived from DUA-restricted data.**

## Why that matters here

CTformer is MIT-licensed, so redistributing the files is permitted by its
licence. The open question is not the licence but the DUA: whether model weights
derived from Mayo challenge data may be redistributed by a third party. The
CTformer authors publish them openly, so if it was theirs to do it is ours to
mirror — but the exposure is inherited rather than independently established.

Fetching rather than mirroring removes the question entirely at no cost to
reproducibility: the bytes come from the authors' own repository.

## Fetch

    ./fetch.sh

Verifies against the SHA256 of the copy this project used, so a fetch that
returns different bytes is reported rather than silently accepted:

    1d9a459b0876582af60f612cdcc239afd856320fda7b69f516b9cea497b4bfb4  T2T_vit_530000iter.ckpt
    67d7de15894da7a58cb1dff0a830ee9c3cbe43f290a4c432aeb978b92f59ff37  loss_530000_iter.npy

If upstream has since retrained, the hash will differ and the v0.5 CTformer
numbers will no longer be reproducible from the fetched file. Say so in that
case rather than updating the hash.
