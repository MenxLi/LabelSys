
#define TRUE 1
#define FALSE 0

typedef unsigned char bool;
typedef unsigned char arr_t;
typedef unsigned char msk_t;
typedef int coord_t;



/* 
 *
 * dst - destination color mask with length im_h*im_w*3
 * msks - src bool masks with length n_msks*im_h*im_w
 * colors - aim colors with length n_msks*3
 *
 * */
void mergeBool2Color2D( arr_t * dest, msk_t * msks, arr_t * colors, int im_h, int im_w, int n_msks ){

    arr_t * dst;
    arr_t * color;
    msk_t * msk;

    bool FIND_COLOR;

    // traverse all pixels
    for (int row = 0; row<im_h; row++){
        for (int col = 0; col < im_w; col ++){

            // initializa find color flag
            FIND_COLOR = FALSE;

            // dest pointer
            dst = dest + (row*im_w + col)*3;

            // traverse all masks at (row, col)
            for (int m=0; m<n_msks; m++){
                // the mask pointer
                msk = msks + m*(im_h*im_w) + row*im_w + col;
                if (*msk == 1){
                    // get the color and jump off the mask traverse loop
                    color = colors + 3*m;
                    FIND_COLOR = TRUE;
                    break;
                }
            }

            if (FIND_COLOR){
                dst[0] = color[0];
                dst[1] = color[1];
                dst[2] = color[2];
            }
        }
    }
}
