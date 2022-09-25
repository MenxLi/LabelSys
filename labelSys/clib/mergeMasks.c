
# include "common.h"
# include <stdlib.h>

typedef unsigned char arr_t;
typedef unsigned char msk_t;
typedef int coord_t;

/*
 *
 * n_color: number of colors
 * colors: array of pointers to single colors, length = n_color
 * dest: destination, array of 3 elements
 *
 * */
void fuseColor(int n_color, arr_t ** colors, arr_t * dest){
    // no color situation
    if (n_color == 0){ return; }

    // single color situation
    if (n_color == 1){
        for (int c = 0; c<3; c++){
            dest[c] = colors[0][c];
        }
        return;
    }

    // multi-color situation
    int sum_color[3] = {0, 0, 0};
    // traverse colors
    for (int i = 0; i<n_color; i++){
        for (int c = 0; c<3; c++){
            sum_color[c] += colors[i][c];
        }
    }
    // set the destination
    for (int c = 0; c<3; c++){
        dest[c] = sum_color[c]/n_color;
    }
}

/* 
 *
 * dst - destination color mask with length im_h*im_w*3
 * msks - src bool masks with length n_msks*im_h*im_w
 * colors - aim colors with length n_msks*3
 *
 * */
EXPORT void mergeBool2Color2D( arr_t * dest, msk_t * msks, arr_t * colors, int im_h, int im_w, int n_msks ){

    arr_t * dst;
    arr_t * color;
    msk_t * msk;

    // selected colors at certain pixel
    // the selected colors will be fused to get final color on the mask
    unsigned int n_sel_colors;
    arr_t ** sel_colors = malloc( sizeof(arr_t*) * n_msks );

    // traverse all pixels
    for (int row = 0; row<im_h; row++){
        for (int col = 0; col < im_w; col ++){

            // dest pointer
            dst = dest + (row*im_w + col)*3;

            // traverse all masks at (row, col)
            n_sel_colors = 0;
            for (int m=0; m<n_msks; m++){
                // the mask pointer
                msk = msks + m*(im_h*im_w) + row*im_w + col;
                if (*msk == 1){
                    color = colors + 3*m;
                    sel_colors[n_sel_colors] = color;
                    n_sel_colors += 1;
                    /* dst[0] = color[0]; */
                    /* dst[1] = color[1]; */
                    /* dst[2] = color[2]; */
                }
            }
            fuseColor(n_sel_colors, sel_colors, dst);
        }
    }
    free(sel_colors);
}
