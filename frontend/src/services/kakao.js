// 카카오 주소 검색 (프론트엔드에서 직접 호출)
export const searchAddressKakao = (address) => {
  return new Promise((resolve, reject) => {
    const geocoder = new window.kakao.maps.services.Geocoder();
    geocoder.addressSearch(address, (result, status) => {
      if (status === window.kakao.maps.services.Status.OK) {
        resolve({
          lat: parseFloat(result[0].y),
          lon: parseFloat(result[0].x),
          jibun_address: result[0].address_name,
          road_address: result[0].road_address?.address_name || '',
        });
      } else {
        reject(new Error('주소를 찾을 수 없습니다.'));
      }
    });
  });
};