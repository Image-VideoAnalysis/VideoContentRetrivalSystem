<script>
  import ImageGrid from '../components/ImageGrid.svelte';

  let results = [
    {
      url: "img_placeholder.png",
      title: "Scene 1",
      video_id: "abc123",
      start_time: 10.5,
      end_time: 15.2
    },
    {
      url: "img_placeholder.png",
      title: "Scene 2",
      video_id: "xyz789",
      start_time: 22.0,
      end_time: 27.3
    },
    {
      url: "img_placeholder.png",
      title: "Scene 3",
      video_id: "def456",
      start_time: 30.1,
      end_time: 35.4
    },
    {
      url: "img_placeholder.png",
      title: "Scene 4",
      video_id: "ghi012",
      start_time: 40.0,
      end_time: 45.5
    },
    {
      url: "img_placeholder.png",
      title: "Scene 5",
      video_id: "jkl345",
      start_time: 50.2,
      end_time: 55.8
    },
    {
      url: "img_placeholder.png",
      title: "Scene 6",
      video_id: "mno678",
      start_time: 60.3,
      end_time: 65.9
    },
    {
      url: "img_placeholder.png",
      title: "Scene 7",
      video_id: "pqr901",
      start_time: 70.4,
      end_time: 75.6
    },
    {
      url: "img_placeholder.png",
      title: "Scene 8",
      video_id: "stu234",
      start_time: 80.5,
      end_time: 85.7
    }
  ];

</script>


<ImageGrid images={results} />

