
# include "common.h"
# include <stdlib.h>
# include <time.h>
# include <stdio.h>

typedef unsigned char arr_t;
typedef unsigned char msk_t;
typedef int coord_t;


__global__ void kernel_fuseColor(arr_t * ddest, msk_t * dmsks, arr_t * dcolors, int im_h, int im_w, int n_msks){

    int i = blockDim.x * blockIdx.x + threadIdx.x;
    if (i >= im_h * im_w){
        return;
    }

    arr_t * dst = ddest + i*3;
    msk_t * msk;
    arr_t * color;

    float sum_color[3] = {0, 0, 0};
    int counter = 0;

    for (int m = 0; m<n_msks; m++){
        msk = dmsks + (im_h*im_w)*m + i;
        if (*msk == 1){
            color = dcolors + 3*m;
            sum_color[0] += color[0];
            sum_color[1] += color[1];
            sum_color[2] += color[2];
            counter++;
        }
    }
    if (counter > 0){
        dst[0] = sum_color[0]/counter;
        dst[1] = sum_color[1]/counter;
        dst[2] = sum_color[2]/counter;
    }
}

extern "C"{
/* 
 *
 * dst - destination color mask with length im_h*im_w*3
 * msks - src bool masks with length n_msks*im_h*im_w
 * colors - aim colors with length n_msks*3
 *
 * */
EXPORT void mergeBool2Color2D( arr_t * dest, msk_t * msks, arr_t * colors, int im_h, int im_w, int n_msks ){
    arr_t* ddest;
    msk_t* dmsks;
    arr_t* dcolors;

    int nbytes_dest = sizeof(arr_t)*im_h*im_w*3;
    int nbytes_msks = sizeof(msk_t)*n_msks*im_h*im_w;
    int nbytes_colors = sizeof(arr_t)*n_msks*3;

    clock_t start_time, end_time;

    start_time = clock();
    cudaMalloc(&ddest, nbytes_dest);
    cudaMalloc(&dmsks, nbytes_msks);
    cudaMalloc(&dcolors, nbytes_colors);
    end_time = clock();
    // printf("Time for cuda allocating memories: %fs\n", (float)(end_time - start_time)/CLOCKS_PER_SEC);

    start_time = clock();
    cudaMemcpy(ddest, dest, nbytes_dest, cudaMemcpyHostToDevice);
    cudaMemcpy(dmsks, msks, nbytes_msks, cudaMemcpyHostToDevice);
    cudaMemcpy(dcolors, colors, nbytes_colors, cudaMemcpyHostToDevice);
    end_time = clock();
    // printf("Time for cuda copying memories: %fs\n", (float)(end_time - start_time)/CLOCKS_PER_SEC);

    const int block_size = 1024;
    int n_blocks = im_h*im_w/block_size + 1;
    kernel_fuseColor<<<n_blocks, block_size>>>(ddest, dmsks, dcolors, im_h, im_w, n_msks);

    cudaDeviceSynchronize();
    cudaMemcpy(dest, ddest, nbytes_dest, cudaMemcpyDeviceToHost);

    cudaFree(ddest);
    cudaFree(dmsks);
    cudaFree(dcolors);
}
}
