import sys
sys.path.append(r'/148Dataset/data-chen.shuaiqi/fairseq/fairseq-main/')
import argparse
import logging
import os
import time
import numpy as np
from sklearn.cluster import MiniBatchKMeans
import random
import joblib
from examples.textless_nlp.gslm.speech2unit.pretrained.utils import (
    get_and_dump_features,
    get_features,
)

def get_parser():
    parser = argparse.ArgumentParser(
        description="Learn K-means clustering over acoustic features."
    )

    # Features arguments
    parser.add_argument(
        "--in_features_path", type=str, default=None, help="Features file path"
    )
    parser.add_argument(
        "--feature_type",
        type=str,
        choices=["logmel", "hubert", "w2v2", "cpc"],
        default="hubert",
        help="Acoustic feature type",
    )
    parser.add_argument(
        "--manifest_path",
        type=str,
        # default=r'/148Dataset/data-chen.shuaiqi/MELD/meld/dev_splits_complete',
        # default = r'/148Dataset/data-chen.shuaiqi/IEMOCAP/IEMOCAP_full_release/Session1/sentences/wav/Ses01F_impro01/',
        default = r'/148Dataset/data-chen.shuaiqi/promptTTS/Dataset_16k/totalwav.txt',
        help="Manifest file containing the root dir and file names",
    )
    parser.add_argument(
        "--out_features_path",
        type=str,
        default = r'./',
        help="Features file path to write to",
    )
    parser.add_argument(
        "--checkpoint_path",
        type=str,
        default = r'/148Dataset/data-chen.shuaiqi/hubert/hubert_base_ls960.pt',
        help="Pretrained acoustic model checkpoint",
    )
    parser.add_argument(
        "--layer",
        type=int,
        help="The layer of the pretrained model to extract features from",
        default=-1,
    )
    parser.add_argument(
        "--sample_pct",
        type=float,
        help="Percent data to use for K-means training",
        default=1.0,
    )

    # K-means arguments
    parser.add_argument(
        "--num_clusters", type=int, help="Nubmer of clusters", default=500
    )
    parser.add_argument("--init", default="k-means++")
    parser.add_argument(
        "--max_iter",
        type=int,
        help="Maximum number of iterations for K-means training",
        default=150,
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        help="Batch size for K-means training",
        default=10000,
    )
    parser.add_argument("--tol", default=0.0, type=float)
    parser.add_argument("--max_no_improvement", default=100, type=int)
    parser.add_argument("--n_init", default=20, type=int)
    parser.add_argument("--reassignment_ratio", default=0.5, type=float)
    parser.add_argument('--channel_id', default = None, type = int)
    parser.add_argument(
        "--out_kmeans_model_path",
        type=str,
        default = r'/148Dataset/data-chen.shuaiqi/cvss/k_means_model/km.bin',
        help="Path to save K-means model",
    )
    parser.add_argument('--kmeans_model_path', default = r'/148Dataset/data-chen.shuaiqi/cvss/km.bin', type = str)

    # Leftovers
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed to use for K-means training",
        default=1369,
    )

    return parser

def get_kmeans_model(
    n_clusters,
    init,
    max_iter,
    batch_size,
    tol,
    max_no_improvement,
    n_init,
    reassignment_ratio,
    random_state,
):
    return MiniBatchKMeans(
        n_clusters=n_clusters,
        init=init,
        max_iter=max_iter,
        batch_size=batch_size,
        tol=tol,
        max_no_improvement=max_no_improvement,
        n_init=n_init,
        reassignment_ratio=reassignment_ratio,
        random_state=random_state,
        verbose=1,
        compute_labels=True,
        init_size=None,
    )

def train_kmeans(kmeans_model, fea_batch):
    start_time = time.time()
    kmeans_model.fit(fea_batch)
    # time_taken = int ((time.time() - start_time // 60, 2))
    return kmeans_model# , time_taken

parser = get_parser()
args = parser.parse_args()
fea_batch = get_features(feature_type = args.feature_type,
                         checkpoint_path = args.checkpoint_path,
                         layer = args.layer,
                         manifest_path = args.manifest_path,
                         sample_pct = args.sample_pct,
                         flatten = True,
                         channel_id = None)
print('fea: ', fea_batch.shape)
kmeans_model = get_kmeans_model(
        n_clusters=args.num_clusters,
        init=args.init,
        max_iter=args.max_iter,
        batch_size=args.batch_size,
        tol=args.tol,
        max_no_improvement=args.max_no_improvement,
        n_init=args.n_init,
        reassignment_ratio=args.reassignment_ratio,
        random_state=args.seed,
    )

kmeans_model = train_kmeans(
        kmeans_model=kmeans_model, fea_batch=fea_batch
    )

os.makedirs(os.path.dirname(args.out_kmeans_model_path), exist_ok=True)
joblib.dump(kmeans_model, open(args.out_kmeans_model_path, "wb"))