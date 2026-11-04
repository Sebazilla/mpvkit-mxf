/* Headless synthetic fixture regression: digest active video/audio bytes, no padding. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/imgutils.h>
#include <libavutil/samplefmt.h>
static uint64_t digest=14695981039346656037ULL;
static long frames=0,samples=0;
static void bytes(const uint8_t *p,int n) { for(int i=0;i<n;i++) { digest^=p[i];digest*=1099511628211ULL; } }
static void drain(AVCodecContext *c, AVFrame *f) {
 int e;
 while((e=avcodec_receive_frame(c,f))>=0) {
  if(c->codec_type==AVMEDIA_TYPE_VIDEO) {
   int n=av_image_get_buffer_size(f->format,f->width,f->height,1);
   if(n<0)exit(12);
   uint8_t *p=av_malloc(n);if(!p)exit(13);
   int got=av_image_copy_to_buffer(p,n,(const uint8_t *const *)f->data,f->linesize,f->format,f->width,f->height,1);
   if(got!=n)exit(14);bytes(p,n);av_free(p);frames++;
  } else {
   int planar=av_sample_fmt_is_planar(f->format),channels=f->ch_layout.nb_channels;
   int n=av_get_bytes_per_sample(f->format)*f->nb_samples*(planar?1:channels);
   for(int i=0;i<(planar?channels:1);i++)bytes(f->extended_data[i],n);
   samples+=f->nb_samples;
  }
  av_frame_unref(f);
 }
 if(e!=AVERROR(EAGAIN)&&e!=AVERROR_EOF)exit(15);
}
int main(int argc,char **argv) {
 if(argc!=2||!getenv("RUSHDECK_CATALOG_DIR"))return 2;
 AVFormatContext *f=NULL; if(avformat_open_input(&f,argv[1],NULL,NULL)<0||avformat_find_stream_info(f,NULL)<0)return 3;
 AVCodecContext **contexts=calloc(f->nb_streams,sizeof(*contexts));
 for(unsigned i=0;i<f->nb_streams;i++) {
  AVCodecParameters *p=f->streams[i]->codecpar;
  if(p->codec_type!=AVMEDIA_TYPE_AUDIO&&p->codec_type!=AVMEDIA_TYPE_VIDEO)continue;
  const AVCodec *codec=avcodec_find_decoder(p->codec_id);if(!codec)return 4;
  contexts[i]=avcodec_alloc_context3(codec);
  if(avcodec_parameters_to_context(contexts[i],p)<0)return 5;
  contexts[i]->thread_count=1;
  if(avcodec_open2(contexts[i],codec,NULL)<0)return 6;
 }
 AVPacket *p=av_packet_alloc();AVFrame *frame=av_frame_alloc();int e;
 while((e=av_read_frame(f,p))>=0) {
  AVCodecContext *c=contexts[p->stream_index];
  if(c) { if(avcodec_send_packet(c,p)<0)return 7;drain(c,frame); }
  av_packet_unref(p);
 }
 if(e!=AVERROR_EOF)return 8;
 for(unsigned i=0;i<f->nb_streams;i++)if(contexts[i]) {
  if(avcodec_send_packet(contexts[i],NULL)<0)return 9;drain(contexts[i],frame);avcodec_free_context(&contexts[i]);
 }
 if(!frames)return 10;
 printf("frames=%ld samples=%ld digest=%016llx\n",frames,samples,(unsigned long long)digest);
 av_frame_free(&frame);av_packet_free(&p);avformat_close_input(&f);free(contexts);return 0;
}
